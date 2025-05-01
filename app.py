import os
import logging
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from extractor import extract_dailymotion_link
from utils import is_valid_url

# Configure logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dailymotion-extractor-secret")

# Set up root path for reverse proxy compatibility
app.config['APPLICATION_ROOT'] = '/'

@app.route('/health')
def health_check():
    """Health check endpoint for Koyeb"""
    return jsonify({
        'status': 'ok',
        'version': '1.0.0',
        'service': 'dailymotion-link-extractor'
    })

@app.route('/')
def index():
    """Render the main page with the form to enter URLs"""
    return render_template('index.html')

@app.route('/extract', methods=['POST'])
def extract():
    """Handle form submission to extract Dailymotion links"""
    url = request.form.get('url', '')
    
    if not url:
        flash('Please enter a URL', 'danger')
        return redirect(url_for('index'))
    
    if not is_valid_url(url):
        flash('Please enter a valid URL', 'danger')
        return redirect(url_for('index'))
    
    try:
        result = extract_dailymotion_link(url)
        if result.get('success'):
            return render_template('result.html', 
                                  success=True, 
                                  dailymotion_link=result.get('link'),
                                  original_url=url)
        else:
            flash(f'Error: {result.get("error")}', 'danger')
            return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"Error extracting link: {str(e)}")
        flash(f'An error occurred: {str(e)}', 'danger')
        return redirect(url_for('index'))

@app.route('/api/extract', methods=['POST'])
def api_extract():
    """API endpoint to extract Dailymotion links"""
    data = request.get_json()
    
    if not data or 'url' not in data:
        return jsonify({'success': False, 'error': 'URL is required'}), 400
    
    url = data['url']
    
    if not is_valid_url(url):
        return jsonify({'success': False, 'error': 'Invalid URL format'}), 400
    
    try:
        result = extract_dailymotion_link(url)
        return jsonify(result)
    except Exception as e:
        logger.error(f"API error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.errorhandler(404)
def page_not_found(e):
    return render_template('index.html', error="Page not found"), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('index.html', error="Internal server error"), 500

if __name__ == '__main__':
    # Get port from environment variable or use 8080 as default
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=True)
