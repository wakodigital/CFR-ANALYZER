[![Netlify Status](https://api.netlify.com/api/v1/badges/d3a5af67-dbf2-421e-a0f4-0d3831f77393/deploy-status)](https://app.netlify.com/projects/melodious-macaron-d6c47b/deploys)


# eCFR Analysis Project

## Overview

The eCFR Analysis Project is a full-stack application that analyzes data from the Electronic Code of Federal Regulations (eCFR) to provide insights into federal agency regulations. It aggregates metrics such as word counts (e.g., Agricultural Marketing Service’s 2,248,679 words for Chapter XI), correction frequencies, and sub-agency ratios, revealing patterns that may indicate inefficiencies, potentially constituting waste, fraud, or abuse. The project uses a SvelteKit frontend hosted on Netlify, a Supabase PostgreSQL backend, and a Python script for data collection.

## Features

- Word Count Metrics: Displays top and bottom 10% of agencies by word count.
- Correction Analysis: Identifies agencies with frequent corrections and rates per 1,000 words.
- Sub-Agency Ratios: Calculates sub-agencies per 1,000 words.
- Recent Corrections: Lists the latest corrections with details like error dates and Federal Register citations.
- Responsive Frontend: Built with SvelteKit, deployed on Netlify for a clean, user-friendly interface.

## Tech Stack
- Frontend: SvelteKit (TypeScript), hosted on Netlify
- Backend: Supabase (PostgreSQL) with custom RPCs for complex queries
- Data Collection: Python script for fetching and processing eCFR data
- Environment Variables: Managed via .env and Netlify for secure Supabase access








