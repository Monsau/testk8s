from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def hello():
    version = os.environ.get('VERSION', '1.0')
    return f'''
    <html>
        <head>
            <title>Hello World</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                }}
                .container {{
                    text-align: center;
                    padding: 40px;
                    background: rgba(255, 255, 255, 0.1);
                    border-radius: 20px;
                    box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
                }}
                h1 {{
                    font-size: 3em;
                    margin-bottom: 20px;
                }}
                .version {{
                    font-size: 1.2em;
                    opacity: 0.8;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🎉 Hello World from Kubernetes! 🎉</h1>
                <p class="version">Version: {version}</p>
                <p>Déployé avec ArgoCD</p>
            </div>
        </body>
    </html>
    '''

@app.route('/health')
def health():
    return {'status': 'healthy'}, 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
