from multiprocessing import Process, Queue
import os
from flask import Flask, jsonify, request
from requests_html import HTMLSession

# Set PUPPETEER_HOME to point to a writable directory
os.environ['PUPPETEER_HOME'] = '/tmp'

app = Flask(__name__)

@app.route('/')
def home():
    return 'Hello, World!'

def fetch_and_render(url, queue):
    try:
        session = HTMLSession()
        response = session.get(url)
        response.html.render()
        data = {
            'headers': dict(response.headers),
            'content': response.html.html,
            'status_code': response.status_code,
            'url': response.url,
        }
        queue.put(data)
    except Exception as e:
        queue.put({'error': str(e)})
    finally:
        session.close()

@app.route('/fetch_html_session', methods=['GET'])
def fetch_html_session():
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'No URL provided'}), 400
    
    queue = Queue()
    process = Process(target=fetch_and_render, args=(url, queue))
    process.start()
    result = queue.get()  # Wait until we have the result from the process
    process.join()

    if 'error' in result:
        # If the result is an error
        return jsonify({'error': result['error']}), 500

    # Return the JSON response with the rendered content
    return jsonify(result)

if __name__ == '__main__':
    app.run()
