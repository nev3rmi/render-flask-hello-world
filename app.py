import asyncio
from quart import Quart, jsonify, request
from requests_html import AsyncHTMLSession

# Create a Quart app instance
app = Quart(__name__)

@app.route('/')
async def home():
    return 'Hello, World!'

@app.route('/fetch_html_session', methods=['GET'])
async def fetch_html_session():
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    try:
        # Create an AsyncHTMLSession object
        session = AsyncHTMLSession()

        # Fetch the content of the URL
        response = await session.get(url)
        
        # Render the JavaScript on the page
        await response.html.arender()

        # Close the session
        await session.close()

        # Build the JSON response
        output = {
            'headers': dict(response.headers),
            'content': response.html.html,
            'status_code': response.status_code,
            'url': response.url
        }

        return jsonify(output)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Check if we're the main module
if __name__ == '__main__':
    app.run()
