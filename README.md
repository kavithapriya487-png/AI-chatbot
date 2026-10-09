# Nova AI assistant

Nova turns the LangGraph chatbot into a responsive website. It can answer general questions and use Wikipedia and arXiv; live web search is enabled when a Tavily API key is configured. The Groq and Tavily keys stay on the server and are never sent to the browser.

## Run it locally

1. Install Python 3.11 or newer.
2. From the project root, install the dependencies into the existing `.venv`:

   ```powershell
   .\.venv\Scripts\python.exe -m pip install -r .\langraph\requirements.txt
   ```

3. Create a `.env` file in the project root (next to this README):

   ```env
   GROQ_API_KEY=your_groq_api_key
   TAVILY_API_KEY=your_tavily_api_key
   ```

   Get API keys from [Groq](https://console.groq.com/keys) and [Tavily](https://app.tavily.com/). Groq is required. Tavily is optional; without it, web search is disabled.

4. Start the website from the project root:

   ```powershell
   .\.venv\Scripts\python.exe -m flask --app .\langraph\app run --debug
   ```

5. Open <http://127.0.0.1:5000>.

## Deploy to Vercel

1. Push the project to GitHub. Do not commit `.env`; `.gitignore` excludes it.
2. In Vercel, import the GitHub repository.
3. Set the Vercel project's **Root Directory** to `langraph`.
4. In **Settings → Environment Variables**, add `GROQ_API_KEY`. Add `TAVILY_API_KEY` for web search (optional).
5. Deploy or redeploy the project. The project includes Vercel's Python function configuration and serves browser assets from `langraph/public`.
6. Open the deployment URL and try a chat. If it fails, check the deployment's **Functions** logs; the browser's developer console and Network panel can also show whether `/api/chat` returned an error.

The app keeps conversation history in each visitor's browser. The model API is called by the server, so the API keys are not exposed to visitors. Configure billing and usage limits on your Groq and Tavily accounts before sharing a public URL; anyone with access to the site can send requests that use your API quota.

The local address only works while the development server is running on your computer. If `.venv` is missing, create it with `py -m venv .venv` before installing the dependencies.
