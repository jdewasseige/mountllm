# MountLLM: Fine-tuning LLMs on Mountaineering Data

## 🏔️ Project Overview

This project aims to fine-tune open-source language models (starting with GPT-OSS-20B) on high-quality mountaineering data from [Camptocamp.org](https://www.camptocamp.org/). The goal is to create a specialized model that excels at understanding alpine terrain, route descriptions, and mountaineering knowledge.

## 🎯 Objectives

- **Data Collection**: Scrape collaborative mountaineering content from Camptocamp.org's open API
- **Dataset Creation**: Transform raw data into instruction-tuning format (prompt-response pairs)
- **Model Fine-tuning**: Fine-tune open-source LLMs on the curated dataset
- **Evaluation**: Assess model performance on mountaineering-specific tasks

## 📋 Implementation Plan

### Phase 1: Data Collection & Initial Processing ✅

- [X] Set up project structure with uv
- [X] Implement Camptocamp.org API client
- [X] Scrape collaborative content (routes, summits, huts, articles)
- [X] Filter for CC-BY-SA licensed content only
- [X] Basic data cleaning and validation
- [X] Export to JSONL format

### Phase 2: Dataset Creation & Prompt Engineering

- [ ] Design prompt templates for various mountaineering tasks
- [ ] Generate instruction-tuning format samples
- [ ] Create diverse task types (summarization, Q&A, extraction, instruction generation)
- [ ] Quality filtering and deduplication
- [ ] Manual review of sample outputs

### Phase 3: Dataset Splitting & Validation

- [ ] Split data into train/validation/test sets (80/10/10)
- [ ] Stratified sampling by task type and content category
- [ ] Dataset statistics and analysis
- [ ] Create dataset cards and metadata
- [ ] Create `DataLoader`

### Phase 4: Model Fine-tuning

- [ ] Set up training infrastructure
- [ ] Configure LoRA/QLoRA parameters
- [ ] Implement training pipeline
- [ ] Monitor training metrics
- [ ] Model checkpointing and evaluation

### Phase 5: Evaluation & Deployment

- [ ] Evaluate on mountaineering-specific benchmarks
- [ ] Human evaluation of outputs
- [ ] Model optimization and iteration
- [ ] Documentation and model card creation

## 🛠️ Tools & Technologies

- **Python 3.13+** with uv package management
- **Camptocamp.org Open API** for data collection
- **torch** for model fine-tuning
- **Pydantic** for data validation
- **aiohttp** for async API requests
- **JSONL** format for dataset storage
- **scikit-learn** for data splitting

## 📊 Data Sources

### Camptocamp.org API Endpoints

- `/routes` - Climbing routes and approaches
- `/summits` - Mountain peaks and summits
- `/huts` - Mountain huts and refuges
- `/waypoints` - Access points and landmarks
- `/articles` - Collaborative articles and guides
- `/climbing_sites` - Climbing areas and crags

### Content Filtering Criteria

- **License**: CC-BY-SA only (collaborative content)
- **Language**: French and English content
- **Quality**: Well-documented routes with descriptions
- **Exclusion**: Personal outings, incident reports, private content

## 🎭 Task Types for Instruction Tuning

1. **Route Summarization**: Condense detailed route descriptions
2. **Difficulty Assessment**: Extract and explain grading systems
3. **Safety Information**: Identify hazards and safety considerations
4. **Access Information**: Provide approach details and logistics
5. **Technical Details**: Extract elevation, orientation, exposure data
6. **Multi-language Translation**: French ↔ English route descriptions
7. **Route Comparison**: Compare similar routes or approaches
8. **Seasonal Considerations**: Identify best climbing seasons

## 📁 Project Structure

```
mountllm/
├── README.md                 # This file
├── pyproject.toml           # Project configuration
├── main.py                  # Main entry point
├── src/                     # Source code
│   ├── __init__.py
│   ├── api/                 # API client modules
│   │   ├── __init__.py
│   │   ├── camptocamp.py   # Camptocamp API client
│   │   └── models.py       # Data models
│   ├── data/                # Data processing
│   │   ├── __init__.py
│   │   ├── collector.py    # Data collection logic
│   │   ├── processor.py    # Data processing pipeline
│   │   └── templates.py    # Prompt templates
│   └── utils/               # Utility functions
│       ├── __init__.py
│       └── helpers.py      # Helper functions
├── data/                    # Data storage
│   ├── raw/                # Raw API responses
│   ├── processed/          # Processed datasets
│   └── final/              # Final train/val/test splits
├── notebooks/               # Jupyter notebooks for exploration
└── tests/                   # Test files
```

## 🚀 Getting Started

### Prerequisites

- Python 3.13+
- uv package manager

### Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd mountllm

# Install dependencies
uv sync

# Run the data collection
python main.py
```

### Environment Variables

Create a `.env` file for configuration:

```bash
# Camptocamp API settings
CAMPTOCAMP_API_BASE_URL=https://api.camptocamp.org
CAMPTOCAMP_USER_AGENT=MountLLM-DataCollector/1.0
CAMPTOCAMP_RATE_LIMIT=100  # requests per minute

# Data collection settings
MAX_ITEMS_PER_CATEGORY=1000
OUTPUT_DIR=./data
```

## 📈 Progress Tracking

- [X] **Phase 1**: Basic project setup and data collection
- [ ] **Phase 2**: Dataset creation and prompt engineering
- [ ] **Phase 3**: Data splitting and validation
- [ ] **Phase 4**: Model fine-tuning
- [ ] **Phase 5**: Evaluation and deployment

## 🤝 Contributing

This project follows collaborative development practices. Please ensure all contributions:

- Respect Camptocamp.org's terms of service and licensing
- Include proper attribution for data sources
- Follow the established code style and testing practices

## 📄 License

This project is licensed under the MIT License. The training data follows Camptocamp.org's CC-BY-SA license terms.

## 🙏 Acknowledgments

- [Camptocamp.org](https://www.camptocamp.org/) for providing the open API and collaborative mountaineering content
- The open-source AI community for fine-tuning methodologies and tools
- Contributors and beta testers for feedback and improvements

---

*Built with ❤️ for the mountaineering and AI communities*
