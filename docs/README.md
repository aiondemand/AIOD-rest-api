# 🇪🇺 AI-on-Demand Metadata Catalogue

The AI-on-Demand Metadata Catalogue provides a unified view of AI assets and resources stored across the AI landscape.
It collects metadata from platforms such as [_Hugging Face_](https://huggingface.co), [_OpenML_](https://openml.org), and [_Zenodo_](https://zenodo.org),
and is connected to European projects like [Bonsapps](https://bonsapps.eu) and [AIDA](https://www.i-aida.org).
Metadata of datasets, models, papers, news, and more from all of these sources is available through a REST API at [api.aiod.eu](https://api.aiod.eu/).

**🧑‍🔬 For most users:**
Many users will only use the REST API indirectly, for example;
through the [Python SDK](https://aiondemand.github.io/aiondemand/) to access all (meta)data in Python scripts, the 
[AIoD website](aiod.eu), including services such as [My Resources](https://github.com/aiondemand/AIOD-marketplace-frontend/) to browse assets,
and [RAIL](https://github.com/aiondemand/aiod-rail) to conduct reproducible ML experiments.
For documentation on how to use the REST API directly, visit the ["Using the API"](https://aiondemand.github.io/AIOD-rest-api/using/) guide.

**🧑‍💻 For service developers:**
To use the metadata catalogue from your service, use the [Python SDK](https://github.com/aiondemand/aiondemand)
or use the REST API directly as detailed in the ["Using the API"](https://aiondemand.github.io/AIOD-rest-api/using/) documentation.

**🌍 Hosting:** For information on how to host the metadata catalogue, see the ["Hosting" documentation](https://aiondemand.github.io/AIOD-rest-api/hosting/).

**🧑‍🔧 API Development:** The ["Developer Guide"](https://aiondemand.github.io/AIOD-rest-api/developer/) has information about the code in this repository and how to make contributions.

### Acknowledgement
Funded by EU’s Horizon Europe research and innovation program under grant agreement [No. 101070000 (AI4EUROPE)](https://cordis.europa.eu/project/id/101070000).
