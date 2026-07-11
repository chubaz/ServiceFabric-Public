FROM node:20-alpine
WORKDIR /app/builder
COPY package*.json ./
# Install dependencies
RUN npm install --legacy-peer-deps
# Copy builder, config and management server
COPY builder.js vite.config.ts server.js ./

# Start management server
CMD ["npm", "start"]
