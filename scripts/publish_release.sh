#!/bin/bash
# publish_release.sh
# Automates packaging and uploading a Text-Fabric dataset to GitHub.

# Ensure script stops on first failure
set -e

ORG="cbop-dev"
REPO="tf-vulgate"
DATA_DIR="tf"
VERSION="0.1"
TAG="v$VERSION.1"

echo "=========================================="
echo " Packaging Text-Fabric Dataset for Release"
echo "=========================================="

# 1. Activate the python virtual environment where text-fabric is installed
# Ensure you activate your text-fabric virtual environment before running this script, or uncomment and set this path:
# source path/to/.venv/bin/activate

# 2. Use the official tf-zip tool to safely package the archive with the exact directory structure TF expects.
# It reads from ~/github/$ORG/$REPO/$DATA_DIR/$VERSION and outputs to ~/Downloads/github/$ORG-release/$REPO/
echo "> Running tf-zip..."
tf-zip ${ORG}/${REPO}/${DATA_DIR} -v ${VERSION}

# Stop if tf-zip fails
ZIP_FILE="$HOME/Downloads/github/${ORG}-release/${REPO}/tf-${VERSION}.zip"
if [ ! -f "$ZIP_FILE" ]; then
    echo "ERROR: tf-zip failed to generate $ZIP_FILE"
    exit 1
fi

echo "> Successfully built $ZIP_FILE"

# 3. Create a GitHub Release and attach the zip file
# This assumes you have the GitHub CLI (gh) installed and authenticated.
echo "> Checking if release $TAG exists..."

if gh release view "$TAG" --repo "${ORG}/${REPO}" > /dev/null 2>&1; then
    echo "> Release $TAG already exists. Uploading/Updating the zip asset..."
    # --clobber overwrites the file if it already exists on the release
    gh release upload "$TAG" "$ZIP_FILE" --repo "${ORG}/${REPO}" --clobber
    echo "> Successfully attached the ZIP to the existing release!"
else
    echo "> Creating a new GitHub release $TAG and attaching the initial dataset..."
    gh release create "$TAG" "$ZIP_FILE" \
        --repo "${ORG}/${REPO}" \
        --title "Release $TAG" \
        --notes "Automated release of Clementine Vulgate Text-Fabric Dataset."
    echo "> Publication complete!"
fi

echo "=========================================="
echo " Done! The dataset is live on GitHub."
echo "=========================================="
