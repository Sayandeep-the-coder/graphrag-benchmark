# Copyright (c) 2024-2026 TigerGraph, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import asyncio
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasicCredentials, HTTPAuthorizationCredentials
from pyTigerGraph import TigerGraphConnection, AsyncTigerGraphConnection
from pyTigerGraph.common.exception import TigerGraphException
from requests import HTTPError

from src.graphrag.core.config import (
    db_config,
    security,
)
from src.graphrag.core.metrics.tg_proxy import TigerGraphConnectionProxy
from src.graphrag.core.logs.logwriter import LogWriter

logger = logging.getLogger(__name__)


def get_db_connection_id_token(
    graphname: str,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    async_conn: bool = False
) -> TigerGraphConnectionProxy:
    host = db_config.get("hostname", "http://tigergraph")
    is_cloud = host and "tgcloud.io" in host.lower()
    
    conn_params = {
        "host": host,
        "graphname": graphname,
        "apiToken": credentials.credentials,
        "tgCloud": is_cloud,
        "restppPort": db_config.get("restppPort", "443" if is_cloud else "9000"),
        "gsPort": db_config.get("gsPort", "443" if is_cloud else "14240"),
        "useCert": is_cloud or (host and host.startswith("https://"))
    }

    if async_conn:
        conn = AsyncTigerGraphConnection(**conn_params)
        asyncio.run(conn.customizeHeader(
            timeout=db_config.get("default_timeout", 300) * 1000, responseSize=5000000
        ))
    else:
        conn = TigerGraphConnection(**conn_params)
        conn.customizeHeader(
            timeout=db_config.get("default_timeout", 300) * 1000, responseSize=5000000
        )
        conn = TigerGraphConnectionProxy(conn, auth_mode="token")

    try:
        if async_conn:
            asyncio.run(conn.gsql("USE GRAPH " + graphname))
        else:
            conn.gsql("USE GRAPH " + graphname)
    except (HTTPError, TigerGraphException):
        LogWriter.error("Failed to connect to TigerGraph. Incorrect ID Token.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    LogWriter.info("Connected to TigerGraph with ID Token")
    return conn


def get_db_connection_pwd(
    graphname, credentials: Annotated[HTTPBasicCredentials, Depends(security)],
    async_conn: bool = False
) -> TigerGraphConnectionProxy:
    conn = elevate_db_connection_to_token(
        db_config.get("hostname"), credentials.username, credentials.password, graphname, async_conn
    )

    if async_conn:
         asyncio.run(conn.customizeHeader(
            timeout=db_config.get("default_timeout", 300) * 1000, responseSize=5000000
        ))
    else:
        conn.customizeHeader(
            timeout=db_config.get("default_timeout", 300) * 1000, responseSize=5000000
        )
        conn = TigerGraphConnectionProxy(conn)
    
    LogWriter.info("Connected to TigerGraph with password")
    return conn


def get_db_connection_pwd_manual(
    graphname, username: str, password: str,
    async_conn: bool = False
) -> TigerGraphConnectionProxy:
    """
    Manual auth - pass in user/pass not from basic auth
    """
    conn = elevate_db_connection_to_token(
        db_config.get("hostname"), username, password, graphname, async_conn
    )

    if async_conn:
         asyncio.run(conn.customizeHeader(
            timeout=db_config.get("default_timeout", 300) * 1000, responseSize=5000000
        ))
    else:
        conn.customizeHeader(
            timeout=db_config.get("default_timeout", 300) * 1000, responseSize=5000000
        )
        conn = TigerGraphConnectionProxy(conn)
    
    LogWriter.info("Connected to TigerGraph with password")
    return conn


def elevate_db_connection_to_token(host: str, username: str, password: str, graphname: str, async_conn: bool = False):
    """Elevate a username/password connection to a token-based connection."""
    is_cloud = host and "tgcloud.io" in host.lower()
    
    # Defaults
    default_restpp = "443" if is_cloud else "9000"
    default_gs = "443" if is_cloud else "14240"
    
    restppPort = db_config.get("restppPort", default_restpp)
    gsPort = db_config.get("gsPort", default_gs)
    
    apiToken = db_config.get("apiToken")
    
    conn_params = {
        "host": host,
        "username": username,
        "password": password,
        "graphname": graphname,
        "restppPort": restppPort,
        "gsPort": gsPort,
        "tgCloud": is_cloud,
        "useCert": is_cloud or (host and host.startswith("https://"))
    }

    if apiToken:
        LogWriter.info("Using pre-configured apiToken from db_config")
        conn_params["apiToken"] = apiToken
    elif db_config.get("getToken"):
        LogWriter.info("getToken is True, requesting new token from server")
        # Create temp sync connection to get token
        tmp_conn = TigerGraphConnection(
            host=host,
            username=username,
            password=password,
            graphname=graphname,
            restppPort=restppPort,
            gsPort=gsPort,
            tgCloud=is_cloud,
            useCert=is_cloud or (host and host.startswith("https://"))
        )
        try:
            token_resp = tmp_conn.getToken()
            if isinstance(token_resp, list) and len(token_resp) > 0:
                apiToken = token_resp[0]
            else:
                apiToken = token_resp
            conn_params["apiToken"] = apiToken
        except HTTPError as e:
            LogWriter.error(f"Failed to get token: HTTP error {e.response.status_code}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Basic"},
            )
        except TigerGraphException as e:
            LogWriter.error(f"Failed to get token: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Failed to get token: {str(e)}"
            )
        except Exception as e:
            LogWriter.error(f"Unexpected error getting token: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error getting token: {str(e)}"
            )

    if async_conn:
        conn = AsyncTigerGraphConnection(**conn_params)
        # Fix for cloud environments where restppPort == gsPort
        if conn.restppPort == conn.gsPort and "/restpp" not in conn.restppUrl:
             conn.restppUrl = conn.restppUrl.rstrip("/") + "/restpp"
        return conn
    else:
        return TigerGraphConnection(**conn_params)


def get_schema_ver(conn: TigerGraphConnectionProxy) -> int:
    """Retrieves the schema version of the graph by running an interpreted query."""
    logger.info("entry: _get_schema_ver")

    query_text = f'INTERPRET QUERY () FOR GRAPH {conn.graphname} {{ PRINT "OK"; }}'

    try:
        if conn._version_greater_than_4_0():
            ret = conn._post(conn.gsUrl + "/gsql/v1/queries/interpret",
                            params={}, data=query_text, authMode="pwd", resKey="version",
                            headers={'Content-Type': 'text/plain'})
        else:
            ret = conn._post(conn.gsUrl + "/gsqlserver/interpreted_query", data=query_text,
                            params={}, authMode="pwd", resKey="version")

        schema_version_int = None
        if isinstance(ret, dict) and "schema" in ret:
            schema_version = ret["schema"]
            try:
                schema_version_int = int(schema_version)
            except (ValueError, TypeError):
                logger.warning(f"Schema version '{schema_version}' could not be converted to integer")
        
        logger.info("exit: _get_schema_ver")
        return schema_version_int

    except Exception as e:
        logger.error(f"Error getting schema version: {str(e)}")
        raise Exception(f"Failed to get schema version: {str(e)}")

