# Web Scraper
Web Scraping to fetch people based on requirements from various social platforms like Twitter, LinkedIn, Tiktok and Facebook.
This tool takes a keyword and based on that it will search for posts/tweets on the social platforms. It will fetch user profiles and then using Google Gemini model it will check the user profile for respective requirement and update google sheet

## Getting Started
1. Clone this repository to your local machine.
2. Install the required dependencies by running pip install -r requirements.txt.
3. Duplicate the sample.env file, rename it to env.env and update the credentials.
4. Create a service account in google project, generate credentials and add credentials.json to the project root directory.

## Technologies Used
1. Python( >3.8.10 )
2. Google Gemnini

## License
This project is licensed under the MIT License. See the LICENSE file for details.
