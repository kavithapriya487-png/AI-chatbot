# Nova AI assistant

Nova turns the LangGraph chatbot into a responsive website. It can answer general questions and use Wikipedia and arXiv; live web search is enabled when a Tavily API key is configured. The Groq and Tavily keys stay on the server and are never sent to the browser.

## Run it locally

1. Install Python 3.11 or newer.
2. Open a terminal in `langraph` and install the dependencies:

   ```powershell
   py -m pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root (next to this README):

   ```env
   GROQ_API_KEY=your_groq_api_key
   TAVILY_API_KEY=your_tavily_api_key
   ```

   Get API keys from [Groq](https://console.groq.com/keys) and [Tavily](https://app.tavily.com/). Groq is required. Tavily is optional; without it, web search is disabled.

4. Start the website from the `langraph` directory:

   ```powershell
   py -m flask --app app run --debug
   ```

5. Open <http://127.0.0.1:5000>.

## Share it as a website

Deploy the project to a Python web host such as Render:

1. Push the project to a private or public GitHub repository. Do not commit `.env`; `.gitignore` excludes it.
2. Create a **Web Service** on Render and connect the repository.
3. Set the service's **Root Directory** to `langraph`.
4. Set the build command to `pip install -r requirements.txt`.
5. Set the start command to `gunicorn app:app`.
6. Add `GROQ_API_KEY` and `TAVILY_API_KEY` as environment variables in the host's dashboard. Never put these values in the frontend or in a committed file.
7. Deploy, then share the public URL with your friend.

The app keeps conversation history in each visitor's browser. The model API is called by the server, so the API keys are not exposed to visitors. Configure billing and usage limits on your Groq and Tavily accounts before sharing a public URL; anyone with access to the site can send requests that use your API quota.
