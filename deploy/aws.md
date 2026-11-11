# Deploying RegTrace on AWS (single EC2 instance)

The simplest setup that is honest to describe as "deployed on AWS".

1. Launch an EC2 instance (Ubuntu 24.04, t3.medium; Neo4j needs ~2 GB RAM).
   Security group: allow 22 from your IP only, and 8080 (web).
   Do not open 5432, 7474 or 7687 to the internet.
2. SSH in and install Docker:
   `sudo apt update && sudo apt install -y docker.io docker-compose-v2 && sudo usermod -aG docker $USER`
3. `git clone https://github.com/karunprem45/regtrace && cd regtrace`
4. Create `.env` with POSTGRES_PASSWORD, NEO4J_PASSWORD, ANTHROPIC_API_KEY. Never commit it.
5. `docker compose up -d --build`
6. Load data inside the api container:
   `docker compose exec api python -m regtrace.pipeline ingest --product-code DQA`
   then `summaries`, `predicates --llm`, `graph --llm` with the same product code.
7. Open http://<public-ip>:8080. Stop the instance when you are not demoing it.

Set a billing alarm before step 1. Anthropic API calls are billed separately.
