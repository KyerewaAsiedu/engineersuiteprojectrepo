"""Shared Streamlit layout helpers for the engineering suite."""

from __future__ import annotations

import streamlit as st


def apply_page_style() -> None:
    """Inject compact CSS so metric cards and captions look consistent."""
    st.markdown(
        """
        <style>
        .block-container {padding-top: 1.4rem; padding-bottom: 2rem; max-width: 1200px;}
        div[data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid #d5dee8;
            border-radius: 12px;
            padding: 12px 14px;
        }
        .hero-kicker {
            color: #0E7C7B;
            font-weight: 700;
            letter-spacing: 0.08em;
            font-size: 0.78rem;
            text-transform: uppercase;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
