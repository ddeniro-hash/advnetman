pipeline {
    agent any

    environment {
        PATH = "${PATH}:/var/lib/jenkins/.local/bin"
    }

    stages {
        stage('Install Dependencies') {
            steps {
                // Ensure that Python and pip are available
                sh 'python3 -m pip install --upgrade pip'
                sh 'pip install --upgrade netmiko'
                sh 'pip install --upgrade flask'
                sh 'pip install --upgrade glob'
                sh 'pip install --upgrade yaml'
                
                // Install Black and Pylint
                sh 'pip install black pylint'
            }
        }

        stage('Check Code Format with Black') {
            steps {
                script {
                    // Run Black to check the code format on all .py files
                    def blackCheck = sh(script: 'black --check **/*.py', returnStatus: true)
                    if (blackCheck != 0) {
                        // If there are formatting issues, reformat the code
                        sh 'black **/*.py'
                        echo "Code has been reformatted by Black."
                    } else {
                        echo "Code format check passed."
                    }
                }
            }
        }

        stage('Run Pylint') {
            steps {
                script {
                    // Run Pylint for static code analysis on all .py files
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
