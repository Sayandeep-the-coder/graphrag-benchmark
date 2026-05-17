FROM node:23.7-slim 
WORKDIR /app

ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"
RUN corepack enable

COPY . .

RUN pnpm install --allow-scripts
RUN pnpm run build
RUN pnpm i -g serve


CMD [ "serve", "-s", "dist" ]
