"""Voice conversation: full-duplex audio through discord-hub's stream.

Layers are swappable by configuration (or live, via /voice commands):
STT (ears), TTS (voice), and the model behind pi (brain). This package
owns transport and interruption policy only — pedagogy stays in the
knowledge base, reached through the same pi session as text.
"""
