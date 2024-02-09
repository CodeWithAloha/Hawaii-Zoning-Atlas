# Description: Dockerfile to build a simple Nginx container
FROM nginx:stable-alpine

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /usr/share/nginx/html

# Make port 80 available to the world outside this container
EXPOSE 80

# Run nginx when the container launches
CMD ["nginx", "-g", "daemon off;"]