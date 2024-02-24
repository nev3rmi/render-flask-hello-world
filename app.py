import os
os.environ['PUPPETEER_HOME'] = '/tmp'

from flask import Flask, jsonify, request
from requests_html import HTMLSession
import requests

import pyppeteer
import asyncio

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
    except requests.exceptions.HTTPError as http_err:
        return jsonify({'error': f'HTTP error occurred: {http_err}'}), 500
    except Exception as err:
        return jsonify({'error': f'An error occurred: {err}'}), 500
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


@app.route('/fetch_html_session', methods=['GET'])
def fetch_html_session():
    # Get the URL from the query parameters
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    # Create an HTML Session object
    session = HTMLSession()
    
    try:
        # Fetch the content of the URL as usual
        response = session.get(url)
        response.raise_for_status()  # Check for HTTP errors
        
        # Render the JavaScript on the page
        response.html.render()
        
        # Since headers might be modified after rendering JavaScript, capture headers again
        modified_headers = {key.replace('-', '_'): value for key, value in response.headers.items()}

        # Build the JSON response with data from the rendered page
        output = {
            'headers': dict(response.headers),
            'modified_headers': modified_headers,
            'content': response.html.html,
            'status_code': response.status_code,
            'url': response.url
        }
        
    except requests.exceptions.HTTPError as http_err:
        return jsonify({'error': f'HTTP error occurred: {http_err}'}), 500
    except Exception as err:
        return jsonify({'error': f'An error occurred: {err}'}), 500
    finally:
        # Make sure to close the session
        session.close()
    
    # Return the JSON response
    return jsonify(output)

# You may need to set up a custom event loop policy to prevent event loop policy errors
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy() if os.name == 'nt' else asyncio.DefaultEventLoopPolicy())
