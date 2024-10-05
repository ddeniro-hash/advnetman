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
                sh 'pip install --upgrade glob2'
                sh 'pip install --upgrade PyYAML'
                sh 'pip install --upgrade black'
                sh 'pip install --upgrade pylint'
            }
        }

        stage('Check Code Format with Black (1st Check)') {
            steps {
                script {
                    // Run Black to check the code format on all .py files
                    def blackCheck = sh(script: 'black --check *.py', returnStatus: true)
                    if (blackCheck != 0) {
                        // If there are formatting issues, reformat the code
                        sh 'black *.py'
                        echo "Code has been reformatted by Black."
                    } else {
                        echo "Code format check passed."
                    }
                }
            }
        }

        stage('Check Code Format with Black (2nd Check)') {
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
                        echo "Pylint found issues in the code:\n${pylintOutput}"
                    } else {
                        echo "Pylint check passed."
                    }
                }
            }
        }
    }

        stage('Push Changes') {
        steps {
            script {
                // Configure git (ensure you have set the correct user email and name)
                sh 'git config --global user.email "dantedeniro24@gmail.com'
                sh 'git config --global user.name "ddeniro-hash"'
                
                // Add changes to staging
                sh 'git add .'
                
                // Commit changes
                sh 'git commit -m "Automated formatting changes by Black" || echo "No changes to commit"'
                
                // Push changes (ensure that the correct credentials are configured)
                sh 'git push origin main'
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
