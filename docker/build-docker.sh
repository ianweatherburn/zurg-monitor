#!/bin/bash
# ============================================================================
# Zurg Monitor - Docker Build Script
# ============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="zurg-monitor"
VERSION="3.0.0"
REGISTRY=""  # Add your registry here if needed (e.g., "ghcr.io/username/")

# Build arguments
BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
VCS_REF=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")

echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║          Zurg Broken Torrent Monitor - Docker Builder               ║${NC}"
echo -e "${CYAN}║                        Version ${VERSION}                              ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════════╝${NC}"
echo

# Function to print section headers
print_section() {
    echo
    echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${MAGENTA}  $1${NC}"
    echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo
}

# Check if Docker is installed
print_section "Checking Prerequisites"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker is not installed${NC}"
    echo -e "${YELLOW}Please install Docker: https://docs.docker.com/get-docker/${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker is installed${NC}"

# Check if required files exist
echo -e "${CYAN}Checking required files...${NC}"
required_files=("Dockerfile" "zurg-monitor.py" "zurg-monitor.conf" ".dockerignore")
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo -e "${RED}✗ Required file missing: $file${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Found: $file${NC}"
done

# Ask user what to build
print_section "Build Options"
echo "1. Build for current platform only (fastest)"
echo "2. Build for multiple platforms (amd64, arm64, arm/v7)"
echo "3. Build and push to registry"
echo "4. Build with no cache (clean build)"
echo "5. Build using docker-compose"
read -p "Select option [1-5]: " BUILD_OPTION

case $BUILD_OPTION in
    1)
        BUILD_TYPE="single"
        ;;
    2)
        BUILD_TYPE="multi"
        ;;
    3)
        BUILD_TYPE="push"
        read -p "Enter registry URL (e.g., ghcr.io/username/): " REGISTRY
        ;;
    4)
        BUILD_TYPE="nocache"
        ;;
    5)
        BUILD_TYPE="compose"
        ;;
    *)
        echo -e "${RED}Invalid option${NC}"
        exit 1
        ;;
esac

# Build image tags
FULL_IMAGE="${REGISTRY}${IMAGE_NAME}"
TAGS="-t ${FULL_IMAGE}:${VERSION} -t ${FULL_IMAGE}:latest"

# Build based on selection
print_section "Building Docker Image"

case $BUILD_TYPE in
    single)
        echo -e "${CYAN}Building for current platform...${NC}"
        docker build \
            --build-arg BUILD_DATE="${BUILD_DATE}" \
            --build-arg VERSION="${VERSION}" \
            --build-arg VCS_REF="${VCS_REF}" \
            ${TAGS} \
            .
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ Build successful!${NC}"
        else
            echo -e "${RED}✗ Build failed${NC}"
            exit 1
        fi
        ;;
    
    multi)
        echo -e "${CYAN}Building for multiple platforms...${NC}"
        echo -e "${YELLOW}This may take several minutes...${NC}"
        
        # Check if buildx is available
        if ! docker buildx version &> /dev/null; then
            echo -e "${RED}✗ Docker buildx is not available${NC}"
            echo -e "${YELLOW}Please enable buildx: https://docs.docker.com/buildx/working-with-buildx/${NC}"
            exit 1
        fi
        
        # Create builder if it doesn't exist
        if ! docker buildx inspect multiarch &> /dev/null; then
            echo -e "${CYAN}Creating buildx builder...${NC}"
            docker buildx create --name multiarch --use
        else
            docker buildx use multiarch
        fi
        
        docker buildx build \
            --platform linux/amd64,linux/arm64,linux/arm/v7 \
            --build-arg BUILD_DATE="${BUILD_DATE}" \
            --build-arg VERSION="${VERSION}" \
            --build-arg VCS_REF="${VCS_REF}" \
            ${TAGS} \
            --load \
            .
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ Multi-platform build successful!${NC}"
        else
            echo -e "${RED}✗ Build failed${NC}"
            exit 1
        fi
        ;;
    
    push)
        echo -e "${CYAN}Building and pushing to registry...${NC}"
        echo -e "${YELLOW}Registry: ${REGISTRY}${NC}"
        
        # Ask for confirmation
        read -p "Are you sure you want to push to registry? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${YELLOW}Build cancelled${NC}"
            exit 0
        fi
        
        # Build for multiple platforms and push
        if ! docker buildx inspect multiarch &> /dev/null; then
            docker buildx create --name multiarch --use
        else
            docker buildx use multiarch
        fi
        
        docker buildx build \
            --platform linux/amd64,linux/arm64,linux/arm/v7 \
            --build-arg BUILD_DATE="${BUILD_DATE}" \
            --build-arg VERSION="${VERSION}" \
            --build-arg VCS_REF="${VCS_REF}" \
            ${TAGS} \
            --push \
            .
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ Build and push successful!${NC}"
        else
            echo -e "${RED}✗ Build/push failed${NC}"
            exit 1
        fi
        ;;
    
    nocache)
        echo -e "${CYAN}Building with no cache...${NC}"
        docker build \
            --no-cache \
            --build-arg BUILD_DATE="${BUILD_DATE}" \
            --build-arg VERSION="${VERSION}" \
            --build-arg VCS_REF="${VCS_REF}" \
            ${TAGS} \
            .
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ Build successful!${NC}"
        else
            echo -e "${RED}✗ Build failed${NC}"
            exit 1
        fi
        ;;
    
    compose)
        echo -e "${CYAN}Building with docker-compose...${NC}"
        if [ ! -f "docker-compose.yml" ]; then
            echo -e "${RED}✗ docker-compose.yml not found${NC}"
            exit 1
        fi
        
        docker-compose build
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ Build successful!${NC}"
        else
            echo -e "${RED}✗ Build failed${NC}"
            exit 1
        fi
        ;;
esac

# Show image info
print_section "Build Information"
echo -e "${CYAN}Image Name:${NC}     ${FULL_IMAGE}"
echo -e "${CYAN}Version:${NC}        ${VERSION}"
echo -e "${CYAN}Build Date:${NC}    ${BUILD_DATE}"
echo -e "${CYAN}VCS Ref:${NC}       ${VCS_REF}"

# List built images
print_section "Built Images"
docker images | grep "${IMAGE_NAME}" | head -5

# Ask if user wants to test the image
print_section "Testing"
read -p "Do you want to test the image? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${CYAN}Running test...${NC}"
    
    # Create temporary config directory
    TMP_DIR=$(mktemp -d)
    mkdir -p "${TMP_DIR}/config" "${TMP_DIR}/logs"
    
    # Create test config
    cat > "${TMP_DIR}/config/zurg-monitor.conf" << 'EOF'
[zurg]
zurg_url = http://localhost:9999
check_interval = 30
log_file = /logs/zurg-monitor.log
rate_limit = 10
EOF
    
    echo -e "${CYAN}Starting test container...${NC}"
    docker run --rm \
        -v "${TMP_DIR}/config:/config" \
        -v "${TMP_DIR}/logs:/logs" \
        -e RUN_ONCE=true \
        -e DEBUG=true \
        -e ZURG_URL=http://host.docker.internal:9999 \
        "${FULL_IMAGE}:latest" || true
    
    # Cleanup
    rm -rf "${TMP_DIR}"
    
    echo -e "${GREEN}✓ Test complete${NC}"
fi

# Next steps
print_section "Next Steps"
echo "1. Create config and logs directories:"
echo -e "   ${CYAN}mkdir -p config logs${NC}"
echo
echo "2. Create configuration file:"
echo -e "   ${CYAN}nano config/zurg-monitor.conf${NC}"
echo
echo "3. Run the container:"
echo -e "   ${CYAN}docker run -d --name zurg-monitor \\${NC}"
echo -e "   ${CYAN}  --restart unless-stopped \\${NC}"
echo -e "   ${CYAN}  -v \$(pwd)/config:/config \\${NC}"
echo -e "   ${CYAN}  -v \$(pwd)/logs:/logs \\${NC}"
echo -e "   ${CYAN}  -e ZURG_URL=http://zurg:9999 \\${NC}"
echo -e "   ${CYAN}  ${FULL_IMAGE}:latest${NC}"
echo
echo "4. Or use docker-compose:"
echo -e "   ${CYAN}docker-compose up -d${NC}"
echo
echo "5. View logs:"
echo -e "   ${CYAN}docker logs -f zurg-monitor${NC}"
echo

echo -e "${GREEN}Build complete! 🎉${NC}"
echo