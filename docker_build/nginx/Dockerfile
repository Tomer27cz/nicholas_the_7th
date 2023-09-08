# Use the official image as a parent image.
FROM nginx
LABEL authors="Tomer27cz"

# Remove the default Nginx configuration file.
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom configuration file from the current directory.
COPY nginx.conf /etc/nginx/conf.d/