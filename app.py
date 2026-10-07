import os
import uvicorn
import gradio as gr
from backend.server import app

# Minimal Gradio interface mounted at /gradio so HF Gradio SDK health checks pass
with gr.Blocks(title="Household Intelligence") as demo:
    gr.Markdown("### Household Intelligence • Greater Jakarta Rental Valuation Engine")
    gr.Markdown("Dashboard running at root `/`. Explore [Dashboard](/) or [LLM Context](/llms.txt).")

# Mount Gradio onto our FastAPI application
combined_app = gr.mount_gradio_app(app, demo, path="/gradio")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run("app:combined_app", host="0.0.0.0", port=port)
