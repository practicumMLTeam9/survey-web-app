FROM node:20-slim
WORKDIR /app

# Зависимости
COPY package*.json ./
RUN npm ci

# Исходный код
COPY . .

EXPOSE 5173

# Vite dev-сервер
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]