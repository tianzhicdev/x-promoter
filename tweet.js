const crypto = require('crypto');
const https = require('https');
const querystring = require('querystring');
require('dotenv').config();

// OAuth 1.0a helper functions
function percentEncode(str) {
    return encodeURIComponent(str)
        .replace(/!/g, '%21')
        .replace(/'/g, '%27')
        .replace(/\(/g, '%28')
        .replace(/\)/g, '%29')
        .replace(/\*/g, '%2A');
}

function generateNonce() {
    return crypto.randomBytes(32).toString('hex');
}

function generateTimestamp() {
    return Math.floor(Date.now() / 1000).toString();
}

function createSignature(method, url, params, consumerSecret, tokenSecret) {
    // Sort parameters alphabetically
    const sortedParams = Object.keys(params)
        .sort()
        .map(key => `${key}=${percentEncode(params[key])}`)
        .join('&');
    
    // Create signature base string
    const signatureBase = `${method}&${percentEncode(url)}&${percentEncode(sortedParams)}`;
    
    // Create signing key
    const signingKey = `${percentEncode(consumerSecret)}&${percentEncode(tokenSecret)}`;
    
    // Generate HMAC-SHA1 signature
    const hmac = crypto.createHmac('sha1', signingKey);
    hmac.update(signatureBase);
    return hmac.digest('base64');
}

function createAuthHeader(params) {
    const headerParams = Object.keys(params)
        .filter(key => key.startsWith('oauth_'))
        .sort()
        .map(key => `${key}="${percentEncode(params[key])}"`)
        .join(', ');
    
    return `OAuth ${headerParams}`;
}

// Tweet function
async function sendTweet(text) {
    const url = 'https://api.twitter.com/2/tweets';
    const method = 'POST';
    
    // OAuth parameters
    const oauthParams = {
        oauth_consumer_key: process.env.X_API_KEY,
        oauth_token: process.env.X_ACCESS_TOKEN,
        oauth_signature_method: 'HMAC-SHA1',
        oauth_timestamp: generateTimestamp(),
        oauth_nonce: generateNonce(),
        oauth_version: '1.0'
    };
    
    // Generate signature
    const signature = createSignature(
        method,
        url,
        oauthParams,
        process.env.X_API_KEY_SECRETS,
        process.env.X_ACCESS_TOKEN_SECRETS
    );
    
    // Add signature to OAuth params
    oauthParams.oauth_signature = signature;
    
    // Create authorization header
    const authHeader = createAuthHeader(oauthParams);
    
    // Request body
    const body = JSON.stringify({ text });
    
    // Make the request
    return new Promise((resolve, reject) => {
        const options = {
            hostname: 'api.twitter.com',
            path: '/2/tweets',
            method: 'POST',
            headers: {
                'Authorization': authHeader,
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(body)
            }
        };
        
        const req = https.request(options, (res) => {
            let data = '';
            
            res.on('data', (chunk) => {
                data += chunk;
            });
            
            res.on('end', () => {
                if (res.statusCode === 201) {
                    console.log('✅ Test tweet sent successfully!');
                    console.log('Response:', data);
                    resolve(JSON.parse(data));
                } else {
                    console.log('❌ Failed to send tweet');
                    console.log('Error response:', data);
                    reject(new Error(data));
                }
            });
        });
        
        req.on('error', (error) => {
            console.error('Request error:', error);
            reject(error);
        });
        
        req.write(body);
        req.end();
    });
}

// Check if running as test
if (process.argv[2] === 'test') {
    const testMessage = `Test tweet from x-promoter at ${new Date().toISOString()}`;
    console.log('Sending test message to X/Twitter...');
    sendTweet(testMessage).catch(console.error);
} else {
    module.exports = { sendTweet };
}