#!/usr/bin/env groovy

/**
 * buildState - Build State API Wrapper
 * 
 * High-level wrapper for Build State API operations through the bldst CLI.
 * Provides simple methods for tracking build state, artifacts, and variables.
 */

/**
 * Initialize the build state tracking
 * Stores the current build ID in environment for use across stages
 */
def call(Map config = [:]) {
    // Ensure CLI is installed
    if (!bldstCLI.isInstalled()) {
        def version = env.BUILDSTATE_CLI_VERSION ?: 'latest'
        bldstCLI.install(version)
    }
    
    // Verify API connection
    if (!bldstCLI.verifyConnection()) {
        error "Cannot connect to Build State API at ${env.BUILDSTATE_API_URL}"
    }
    
    return this
}

/**
 * Start a new build and register it with the Build State API
 * 
 * @param config Build configuration
 *   - project: Project ID (required)
 *   - name: Build name (default: Job name + build number)
 *   - platform: Platform identifier (e.g., 'aws', 'azure', 'gcp')
 *   - osVersion: OS version identifier
 *   - imageType: Image type identifier
 *   - startState: Initial state code (default: 0)
 *   - metadata: Additional metadata map
 * @return Build ID
 */
def start(Map config) {
    echo "=== Starting Build State Tracking ==="
    
    // Validate required parameters
    if (!config.project) {
        error "project parameter is required"
    }
    
    // Set defaults
    def buildName = config.name ?: "${env.JOB_NAME}-${env.BUILD_NUMBER}"
    def platform = config.platform ?: 'jenkins'
    def startState = config.startState ?: 0
    
    // Build arguments
    def args = [
        project_id: config.project,
        name: buildName,
        platform: platform,
        start_state: startState
    ]
    
    // Add optional parameters
    if (config.osVersion) args.os_version = config.osVersion
    if (config.imageType) args.image_type = config.imageType
    if (config.imageVariant) args.image_variant = config.imageVariant
    if (config.metadata) {
        // Convert metadata map to JSON
        args.metadata = groovy.json.JsonOutput.toJson(config.metadata)
    }
    
    try {
        def output = bldstCLI.exec('build create', args, true)
        def buildId = extractBuildId(output)
        
        // Store build ID in environment for use across stages
        env.BUILDSTATE_BUILD_ID = buildId
        
        echo "✓ Build registered: ${buildId}"
        echo "  Name: ${buildName}"
        echo "  Platform: ${platform}"
        if (config.osVersion) echo "  OS: ${config.osVersion}"
        
        return buildId
        
    } catch (Exception e) {
        error "Failed to start build state tracking: ${e.message}"
    }
}

/**
 * Update the build state
 * 
 * @param stateCode The state code to transition to
 * @param message Optional state message/description
 * @param metadata Optional metadata map
 */
def updateState(Integer stateCode, String message = null, Map metadata = [:]) {
    def buildId = env.BUILDSTATE_BUILD_ID
    
    if (!buildId) {
        error "No active build. Call buildState.start() first."
    }
    
    echo "→ Updating build state to ${stateCode}${message ? ': ' + message : ''}"
    
    def args = [
        build_id: buildId,
        state_code: stateCode
    ]
    
    if (message) args.message = message
    if (metadata) args.metadata = groovy.json.JsonOutput.toJson(metadata)
    
    try {
        bldstCLI.exec('build update-state', args, false)
        echo "✓ State updated to ${stateCode}"
    } catch (Exception e) {
        error "Failed to update build state: ${e.message}"
    }
}

/**
 * Record a build artifact
 * 
 * @param config Artifact configuration
 *   - type: Artifact type (e.g., 'vm-snapshot', 'ami', 'disk-image')
 *   - location: Artifact location/identifier (required)
 *   - stateCode: State code when artifact was created
 *   - isResumable: Whether this artifact can be used for resume
 *   - isFinal: Whether this is a final output artifact
 *   - checksumType: Checksum algorithm (e.g., 'sha256')
 *   - checksumValue: Checksum value
 *   - sizeBytes: Artifact size in bytes
 *   - metadata: Additional metadata map
 */
def recordArtifact(Map config) {
    def buildId = env.BUILDSTATE_BUILD_ID
    
    if (!buildId) {
        error "No active build. Call buildState.start() first."
    }
    
    if (!config.type || !config.location) {
        error "Both 'type' and 'location' are required for artifacts"
    }
    
    echo "→ Recording artifact: ${config.type} at ${config.location}"
    
    def args = [
        build_id: buildId,
        artifact_type: config.type,
        artifact_location: config.location
    ]
    
    // Add optional parameters
    if (config.stateCode) args.state_code = config.stateCode
    if (config.isResumable != null) args.is_resumable = config.isResumable
    if (config.isFinal != null) args.is_final = config.isFinal
    if (config.checksumType) args.checksum_type = config.checksumType
    if (config.checksumValue) args.checksum_value = config.checksumValue
    if (config.sizeBytes) args.size_bytes = config.sizeBytes
    if (config.metadata) args.metadata = groovy.json.JsonOutput.toJson(config.metadata)
    
    try {
        bldstCLI.exec('artifact create', args, false)
        echo "✓ Artifact recorded: ${config.type}"
    } catch (Exception e) {
        error "Failed to record artifact: ${e.message}"
    }
}

/**
 * Set a build variable (for resume context)
 * 
 * @param key Variable key
 * @param value Variable value
 * @param config Additional configuration
 *   - type: Variable type (default: 'string')
 *   - stateCode: State when variable was set
 *   - required: Whether required for resume (default: false)
 *   - sensitive: Whether value is sensitive (default: false)
 */
def setVariable(String key, String value, Map config = [:]) {
    def buildId = env.BUILDSTATE_BUILD_ID
    
    if (!buildId) {
        error "No active build. Call buildState.start() first."
    }
    
    def displayValue = config.sensitive ? '***' : value
    echo "→ Setting variable: ${key} = ${displayValue}"
    
    def args = [
        build_id: buildId,
        key: key,
        value: value,
        variable_type: config.type ?: 'string'
    ]
    
    if (config.stateCode) args.state_code = config.stateCode
    if (config.required != null) args.required_for_resume = config.required
    if (config.sensitive != null) args.is_sensitive = config.sensitive
    
    try {
        bldstCLI.exec('variable set', args, false)
        echo "✓ Variable set: ${key}"
    } catch (Exception e) {
        error "Failed to set variable: ${e.message}"
    }
}

/**
 * Get a build variable value
 * 
 * @param key Variable key
 * @return Variable value or null if not found
 */
def getVariable(String key) {
    def buildId = env.BUILDSTATE_BUILD_ID
    
    if (!buildId) {
        error "No active build. Call buildState.start() first."
    }
    
    try {
        def output = bldstCLI.exec('variable get', [build_id: buildId, key: key], true)
        return output
    } catch (Exception e) {
        echo "Warning: Failed to get variable '${key}': ${e.message}"
        return null
    }
}

/**
 * Mark the build as completed successfully
 * 
 * @param message Optional completion message
 * @param finalState Final state code (default: 999)
 */
def complete(String message = 'Build completed successfully', Integer finalState = 999) {
    def buildId = env.BUILDSTATE_BUILD_ID
    
    if (!buildId) {
        echo "Warning: No active build to complete"
        return
    }
    
    echo "=== Completing Build ==="
    
    try {
        bldstCLI.exec('build complete', [
            build_id: buildId,
            state_code: finalState,
            message: message
        ], false)
        
        echo "✓ Build completed successfully: ${buildId}"
    } catch (Exception e) {
        echo "Warning: Failed to mark build as complete: ${e.message}"
    }
}

/**
 * Mark the build as failed
 * 
 * @param message Failure message (required)
 * @param errorCode Error state code (default: -1)
 */
def fail(String message, Integer errorCode = -1) {
    def buildId = env.BUILDSTATE_BUILD_ID
    
    if (!buildId) {
        echo "Warning: No active build to mark as failed"
        return
    }
    
    echo "=== Build Failed ==="
    
    try {
        bldstCLI.exec('build fail', [
            build_id: buildId,
            state_code: errorCode,
            message: message,
            error_message: message
        ], false)
        
        echo "✓ Build marked as failed: ${buildId}"
    } catch (Exception e) {
        echo "Warning: Failed to record build failure: ${e.message}"
    }
}

/**
 * Resume a build from a previous state
 * 
 * @param buildId Build ID to resume (required)
 * @param resumeFromState State code to resume from
 * @return Resume context data
 */
def resume(String buildId, Integer resumeFromState = null) {
    echo "=== Resuming Build ${buildId} ==="
    
    def args = [build_id: buildId]
    if (resumeFromState) {
        args.from_state = resumeFromState
    }
    
    try {
        def output = bldstCLI.exec('build resume', args, true)
        
        // Store resumed build ID
        env.BUILDSTATE_BUILD_ID = buildId
        
        echo "✓ Build resume data retrieved"
        
        // Parse and return resume context
        def context = parseResumeContext(output)
        return context
        
    } catch (Exception e) {
        error "Failed to resume build: ${e.message}"
    }
}

/**
 * Get build details
 * 
 * @param buildId Build ID (default: current build)
 * @return Build details as map
 */
def getBuildDetails(String buildId = null) {
    buildId = buildId ?: env.BUILDSTATE_BUILD_ID
    
    if (!buildId) {
        error "No build ID specified"
    }
    
    try {
        def output = bldstCLI.exec('build get', [build_id: buildId], true)
        return parseBuildDetails(output)
    } catch (Exception e) {
        error "Failed to get build details: ${e.message}"
    }
}

/**
 * List all artifacts for the current build
 * 
 * @return List of artifact maps
 */
def listArtifacts() {
    def buildId = env.BUILDSTATE_BUILD_ID
    
    if (!buildId) {
        error "No active build. Call buildState.start() first."
    }
    
    try {
        def output = bldstCLI.exec('artifact list', [build_id: buildId], true)
        return parseArtifactList(output)
    } catch (Exception e) {
        error "Failed to list artifacts: ${e.message}"
    }
}

// Helper methods

private String extractBuildId(String output) {
    // Extract build ID from CLI output
    def matcher = output =~ /(?:Build ID|build_id):\s*([a-f0-9-]{36})/
    if (matcher) {
        return matcher[0][1]
    }
    error "Could not extract build ID from output: ${output}"
}

private Map parseResumeContext(String output) {
    try {
        return readJSON(text: output)
    } catch (Exception e) {
        echo "Warning: Could not parse resume context as JSON"
        return [raw: output]
    }
}

private Map parseBuildDetails(String output) {
    try {
        return readJSON(text: output)
    } catch (Exception e) {
        echo "Warning: Could not parse build details as JSON"
        return [raw: output]
    }
}

private List parseArtifactList(String output) {
    try {
        def json = readJSON(text: output)
        return json instanceof List ? json : [json]
    } catch (Exception e) {
        echo "Warning: Could not parse artifact list as JSON"
        return []
    }
}
