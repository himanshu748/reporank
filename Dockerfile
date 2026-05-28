FROM ubuntu:24.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies (Python, curl, git, and pip)
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set workspace directory
WORKDIR /app

# Copy python dependency specifications
COPY requirements.txt .

# Install python dependencies (using --break-system-packages for Ubuntu's managed Python environment)
RUN pip3 install -r requirements.txt --break-system-packages

# Install Coral CLI (version v0.4.0) directly into system bin path
ENV CORAL_VERSION=v0.4.0
ENV CORAL_INSTALL_DIR=/usr/local/bin
RUN curl -fsSL https://withcoral.com/install.sh | sh

# Copy the rest of the application files
COPY . .

# Ensure start.sh has executable permissions
RUN chmod +x start.sh

# Expose port
EXPOSE 8000

# Start server using the start script
CMD ["./start.sh"]
