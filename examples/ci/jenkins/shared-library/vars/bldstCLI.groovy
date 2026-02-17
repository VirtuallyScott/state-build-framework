#!/usr/bin/env groovy

/**
 * bldstCLI - Build State CLI Management
 * 
 * Handles installation, versioning, and execution of the bldst CLI tool.
 * Provides automatic installation with version management and caching.
 */

def call(Map config = [:]) {
    return this
}

/**
 * Install or update the bldst CLI
 * 
 * @param version CLI version to install (default: latest)
 * @param force Force reinstallation even if already installed
 * @return true if successful
 */
def install(String version = 'latest', boolean force = false) {
    def venvPath = "${env.WORKSPACE}/.bldst-venv"
    def markerFile = "${venvPath}/.installed-version"
    
    // Check if already installed with correct version
    if (!force && fileExists(markerFile)) {
        def installedVersion = readFile(markerFile).trim()
        if (version == 'latest' || installedVersion == version) {
            echo "✓ bldst CLI already installed (version: ${installedVersion})"
            return true
        }
    }
    
    echo "Installing bldst CLI (version: ${version})..."
    
    try {
        // Create virtual environment
        sh """
            set -e
            python3 -m venv ${venvPath}
            . ${venvPath}/bin/activate
            
            # Upgrade pip
            pip install --upgrade pip wheel
            
            # Install bldst CLI
            if [ "${version}" = "latest" ]; then
                pip install --upgrade buildstate-cli
            else
                pip install buildstate-cli==${version}
            fi
            
            # Store installed version
            pip show buildstate-cli | grep Version | cut -d: -f2 | tr -d ' ' > ${markerFile}
        """
        
        def installedVersion = readFile(markerFile).trim()
        echo "✓ bldst CLI installed successfully (version: ${installedVersion})"
        return true
        
    } catch (Exception e) {
        error "Failed to install bldst CLI: ${e.message}"
        return false
    }
}

/**
 * Execute a bldst CLI command
 * 
 * @param command The bldst command to execute (e.g., 'build create')
 * @param args Map of command arguments
 * @param returnOutput If true, return command output instead of exit code
 * @return Command output (String) or exit code (Integer)
 */
def exec(String command, Map args = [:], boolean returnOutput = true) {
    def venvPath = "${env.WORKSPACE}/.bldst-venv"
    
    // Ensure CLI is installed
    if (!fileExists("${venvPath}/bin/activate")) {
        install()
    }
    
    // Build command with arguments
    def cmdArgs = buildArgs(args)
    def fullCommand = "bldst ${command} ${cmdArgs}".trim()
    
    // Set environment variables
    def envVars = [
        "BUILDSTATE_API_URL=${env.BUILDSTATE_API_URL ?: ''}",
        "BUILDSTATE_API_KEY=${env.BUILDSTATE_API_KEY ?: ''}"
    ]
    
    if (env.BUILDSTATE_DEBUG == 'true') {
        envVars.add("BUILDSTATE_DEBUG=1")
    }
    
    if (env.BUILDSTATE_TIMEOUT) {
        envVars.add("BUILDSTATE_TIMEOUT=${env.BUILDSTATE_TIMEOUT}")
    }
    
    def envString = envVars.join(' ')
    
    try {
        if (returnOutput) {
            return sh(
                script: """
                    set -e
                    . ${venvPath}/bin/activate
                    ${envString} ${fullCommand}
                """,
                returnStdout: true
            ).trim()
        } else {
            return sh(
                script: """
                    set -e
                    . ${venvPath}/bin/activate
                    ${envString} ${fullCommand}
                """,
                returnStatus: true
            )
        }
    } catch (Exception e) {
        error "Failed to execute bldst command '${fullCommand}': ${e.message}"
    }
}

/**
 * Build command line arguments from a map
 * 
 * @param args Map of argument names to values
 * @return String of formatted arguments
 */
private String buildArgs(Map args) {
    def argList = []
    
    args.each { key, value ->
        if (value == null || value == '') {
            return // skip empty values
        }
        
        def argName = key.toString().replaceAll('_', '-')
        
        if (value instanceof Boolean) {
            if (value) {
                argList.add("--${argName}")
            }
        } else if (value instanceof List) {
            value.each { item ->
                argList.add("--${argName} '${item}'")
            }
        } else {
            argList.add("--${argName} '${value}'")
        }
    }
    
    return argList.join(' ')
}

/**
 * Get the installed CLI version
 * 
 * @return Version string or 'not installed'
 */
def getVersion() {
    def venvPath = "${env.WORKSPACE}/.bldst-venv"
    def markerFile = "${venvPath}/.installed-version"
    
    if (fileExists(markerFile)) {
        return readFile(markerFile).trim()
    }
    return 'not installed'
}

/**
 * Check if CLI is installed
 * 
 * @return true if installed
 */
def isInstalled() {
    def venvPath = "${env.WORKSPACE}/.bldst-venv"
    return fileExists("${venvPath}/bin/activate")
}

/**
 * Clean up CLI installation
 * 
 * Removes the virtual environment and cached installation
 */
def cleanup() {
    def venvPath = "${env.WORKSPACE}/.bldst-venv"
    
    if (fileExists(venvPath)) {
        sh "rm -rf ${venvPath}"
        echo "✓ bldst CLI installation cleaned up"
    }
}

/**
 * Verify API connection
 * 
 * @return true if API is reachable and authenticated
 */
def verifyConnection() {
    try {
        echo "Verifying Build State API connection..."
        exec('health', [:], true)
        echo "✓ API connection verified"
        return true
    } catch (Exception e) {
        echo "✗ API connection failed: ${e.message}"
        return false
    }
}
