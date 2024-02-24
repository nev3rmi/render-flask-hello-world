import os
from flask import Flask, jsonify, request
from requests_html import HTMLSession
import requests
from threading import Thread

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

def fetch_and_render(url, callback):
    try:
        session = HTMLSession()
        response = session.get(url)
        response.html.render()
        session.close()
        callback(response)
    except Exception as e:
        callback(e)

@app.route('/fetch_html_session', methods=['GET'])
def fetch_html_session():
    # Get the URL from the query parameters
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'No URL provided'}), 400
    
    results = {}

    def on_result(response):
        if isinstance(response, Exception):
            results['error'] = str(response)
        else:
            results.update({
                'headers': dict(response.headers),
                'content': response.html.html,
                'status_code': response.status_code,
                'url': response.url
            })
    
    # Create a Thread to fetch and render the page in the background
    thread = Thread(target=fetch_and_render, args=(url, on_result))
    thread.start()
    thread.join()  # Wait for the thread to finish
    
    if 'error' in results:
        return jsonify({'error': results['error']}), 500
    
    # Return the JSON response with the rendered content
    return jsonify(results)
