# Stage 1: Build React application
FROM node:18-alpine AS builder

WORKDIR /app

# Copy dependency configs
COPY package*.json ./

# Install packages
RUN npm ci

# Copy frontend source files
COPY . .

# Compile production bundle (generates dist/ folder)
RUN npm run build

# Stage 2: Serve compiled assets with Nginx
FROM nginx:stable-alpine

# Copy custom routing configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy compiled assets from Stage 1 builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose Nginx port
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
