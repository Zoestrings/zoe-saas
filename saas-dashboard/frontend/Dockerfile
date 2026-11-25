FROM node:20-alpine

WORKDIR /app

ARG NEXT_PUBLIC_API_URL=https://zoe-saas-production.up.railway.app
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
ENV NODE_ENV=production

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

EXPOSE 3000

CMD ["sh", "-c", "npx next start -H 0.0.0.0 -p ${PORT:-3000}"]
