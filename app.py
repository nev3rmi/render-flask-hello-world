import os
from flask import Flask, jsonify, request
from requests_html import HTMLSession
import requests
from threading import Thread
import asyncio

# # Set PUPPETEER_HOME to point to a writable directory
# os.environ['PUPPETEER_HOME'] = '/tmp'

app = Flask(__name__)

@app.route('/')
def home():
    return 'Hello, World!'

@app.route('/fetch', methods=['GET'])
def fetch_url():
    # Get the URL from the query parameters
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'No URL provided'}), 400
    # Fetch the content of the URL
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500
    # Replace all hyphens in header keys with underscores
    modified_headers = {key.replace('-', '_'): value for key, value in response.headers.items()}
    # Build the JSON response with modified headers and content
    output = {
        'headers': dict(response.headers),
        'modified_headers': modified_headers,
        'content': response.text,
        'status_code': response.status_code,
        'url': response.url
    }
    # Return the JSON response
    return jsonify(output)

def run_async_render(url, callback):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    response = None
    try:
        with HTMLSession() as session:
            response = session.get(url)
            loop.run_until_complete(response.html.render())
            # Safely handle session close
            loop.run_until_complete(session.close())
    except Exception as e:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
        callback(e, None)
        return
    loop.run_until_complete(loop.shutdown_asyncgens())
    loop.close()
    callback(None, response)

@app.route('/fetch_html_session', methods=['GET'])
def fetch_html_session():
    url = request.args.get('url')
    results = {}
    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    def on_result(error, response):
        if error:
            results['error'] = str(error)
        else:
            results['headers'] = dict(response.headers)
            results['content'] = response.html.html
            results['status_code'] = response.status_code
            results['url'] = response.url

    # Create a Thread to fetch and render the page
    thread = Thread(target=run_async_render, args=(url, on_result))
    thread.start()
    thread.join()  # Wait for the thread to finish

    if 'error' in results:
        return jsonify({'error': results['error']}), 500

    # Return the JSON response with the rendered content
    return jsonify(results)
