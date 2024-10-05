pipeline {
    agent any

    stages {
        stage('Install Dependencies') {
            steps {
                // Ensure that Python and pip are available
                sh 'python3 -m pip install --upgrade pip'
                sh 'pip install --upgrade netmiko'
                sh 'pip install --upgrade flask'
                sh 'pip install --upgrade glob2' // corrected to glob2
                sh 'pip install --upgrade PyYAML' // corrected to PyYAML
                
                // Install Black and Pylint
                sh 'pip install black pylint'
            }
        }

        stage('Check Code Format with Black') {
            steps {
                // Run Black to check the code format only on .py files
                script {
                    def blackOutput = sh(script: 'black --check **/*.py', returnStatus: true)
                    if (blackOutput != 0) {
                        error "Code format issues found. Please run Black to format your code."
                    } else {
                        echo "Code format check passed."
                    }
                }
            }
        }

        stage('Run Pylint') {
            steps {
                // Run Pylint for static code analysis only on .py files
                script {
                    def pylintOutput = sh(script: 'pylint **/*.py', returnStatus: true)
                    if (pylintOutput != 0) {
                        error "Pylint found issues in the code."
                    } else {
                        echo "Pylint check passed."
                    }
                }
            }
        }
    }

    post {
        always {
            // Clean up actions, such as archiving artifacts or notifying
            echo 'Cleaning up...'
        }
        success {
            echo 'Build completed successfully.'
        }
        failure {
            echo 'Build failed. Please check the logs for details.'
        }
    }
}
