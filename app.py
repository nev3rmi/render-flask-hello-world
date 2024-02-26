from flask import Flask, jsonify, request
from pytrends.request import TrendReq
import requests

app = Flask(__name__)

def get_proxies_from_url(url):
  try:
      response = requests.get(url)
      response.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code
      # Assuming each proxy is in a new line as 'IP:Port'
      proxies = response.text.strip().split('\n')
      return proxies
  except requests.RequestException as e:
      print(f"An error occurred while fetching proxies: {e}")
      return []

proxies = get_proxies_from_url('https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all')

pytrend = TrendReq(hl='en-US', tz=360, timeout=(10,25), proxies=proxies, retries=2, backoff_factor=0.1, requests_args={'verify':False})


# Interest Over Time with Exception Handling
@app.route('/interest_over_time', methods=['GET'])
def interest_over_time():
  try:
    keywords = request.args.get('keywords')
    if not keywords:
      return jsonify({'error': 'No keywords provided'}), 400

    timeframe = request.args.get('timeframe',
                                 'today 5-y')  # Providing a default timeframe
    tgt_geo = request.args.get('geo', '')  # Empty string defaults to worldwide

    pytrend.build_payload(kw_list=keywords.split(','),
                          timeframe=timeframe,
                          geo=tgt_geo)
    data = pytrend.interest_over_time()
    if data.empty:
      return jsonify({'error': 'No data found'}), 404
    return jsonify(data.to_dict())
  except Exception as e:
    # Here you would log error details in a production app
    return jsonify({'error': 'An error occurred', 'details': str(e)}), 500


# Interest by Region
@app.route('/interest_by_region', methods=['GET'])
def interest_by_region():
  keywords = request.args.get('keywords', '').split(',')
  resolution = request.args.get('resolution', 'COUNTRY')

  pytrend.build_payload(kw_list=keywords)
  data = pytrend.interest_by_region(resolution=resolution)
  return jsonify(data.to_dict())


# Related Topics
@app.route('/related_topics', methods=['GET'])
def related_topics():
  keywords = request.args.get('keywords', '').split(',')

  pytrend.build_payload(kw_list=keywords)
  data = pytrend.related_topics()
  return jsonify(data)


# Related Queries
@app.route('/related_queries', methods=['GET'])
def related_queries():
  keywords = request.args.get('keywords', '').split(',')

  pytrend.build_payload(kw_list=keywords)
  data = pytrend.related_queries()
  return jsonify(data)


# Trending Searches
@app.route('/trending_searches', methods=['GET'])
def trending_searches():
  # No keyword is needed, but could accept parameters like `date` and `geo` if the method allows
  data = pytrend.trending_searches()
  return jsonify(data.to_dict())


# Top Charts
@app.route('/top_charts', methods=['GET'])
def top_charts():
  date = request.args.get('date', '')
  geo = request.args.get('geo', '')
  category = request.args.get('category', '')

  data = pytrend.top_charts(date=date, geo=geo, category=category)
  return jsonify(data.to_dict())


# Suggestions
@app.route('/suggestions', methods=['GET'])
def suggestions():
  keyword = request.args.get('keyword', '')
  data = pytrend.suggestions(keyword)
  return jsonify(data)

# Route for displaying the Google Trends data as a json
@app.route('/trends', methods=['GET'])
def google_trends_json():
  keywords = request.args.get('keywords')
  timeframe = request.args.get('timeframe', 'today 5-y')
  geo = request.args.get('geo', '')

  if not keywords:
    return jsonify({'error': 'No keywords provided'}), 400

  pytrend = TrendReq(hl='en-US', tz=0)
  pytrend.build_payload(kw_list=keywords.split(','),
                        timeframe=timeframe,
                        geo=geo)

  try:
    interest_over_time_df = pytrend.interest_over_time()
    if interest_over_time_df.empty:
      return jsonify({'error': 'No results found'}), 404
    return interest_over_time_df.to_json()
  except Exception as e:
    return jsonify({'error': str(e)}), 500


# Check if we're the main module
if __name__ == '__main__':
    app.run()
