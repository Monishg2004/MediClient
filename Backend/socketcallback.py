# socketcallback.py
from typing import Any, Dict, List, Union
from langchain.callbacks.base import BaseCallbackHandler

class SocketIOCallback(BaseCallbackHandler):
    """Callback handler for streaming LLM responses via Socket.IO"""

    def __init__(self, fn):
        """Initialize with the function that will handle the streaming responses"""
        self.fn = fn
        self.current_text = ""

    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str],
                     **kwargs: Any) -> None:
        """Run when LLM starts running."""
        self.current_text = ""

    def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        """Run on new LLM token. Only available when streaming is enabled."""
        self.current_text += token
        self.fn(self.current_text)

    def on_llm_end(self, response: Any, **kwargs: Any) -> None:
        """Run when LLM ends running."""
        self.current_text = ""

    def on_llm_error(self, error: Union[Exception, KeyboardInterrupt],
                     **kwargs: Any) -> None:
        """Run when LLM errors."""
        pass

    def on_chain_start(self, serialized: Dict[str, Any],
                       inputs: Dict[str, Any], **kwargs: Any) -> None:
        """Run when chain starts running."""
        pass

    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> None:
        """Run when chain ends running."""
        pass

    def on_chain_error(self, error: Union[Exception, KeyboardInterrupt],
                       **kwargs: Any) -> None:
        """Run when chain errors."""
        pass

    def on_tool_start(self, serialized: Dict[str, Any], input_str: str,
                      **kwargs: Any) -> None:
        """Run when tool starts running."""
        pass

    def on_tool_end(self, output: str, **kwargs: Any) -> None:
        """Run when tool ends running."""
        pass

    def on_tool_error(self, error: Union[Exception, KeyboardInterrupt],
                      **kwargs: Any) -> None:
        """Run when tool errors."""
        pass

    def on_text(self, text: str, **kwargs: Any) -> None:
        """Run on arbitrary text."""
        pass