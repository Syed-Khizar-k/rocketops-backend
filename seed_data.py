import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rocketops_core.settings')
django.setup()

from api.models import TeamMember, Service, ServiceFeature, Product


def seed():
    # ── 1. Team Members ──────────────────────────────────────────────────────
    team_data = [
        {
            "name": "Sami Zoabi",
            "category": "CEO RocketOps",
            "linkedin_url": "https://www.linkedin.com/in/sami-zoabi-a0048654/",
            "image": "team/sami.png",
        },
        {
            "name": "Syed Umair Ul Hassan",
            "category": "AI Engineer",
            "linkedin_url": "https://www.linkedin.com/in/syed-umair-ul-hassan-03412b100/",
            "image": "team/umair.png",
        },
        {
            "name": "Syed Junaid Ul Hassan",
            "category": "Full Stack Developer",
            "linkedin_url": "https://www.linkedin.com/in/syed-junaid-ul-hassan-892b5324b?utm_source=share&utm_campaign=share_via&utm_content=profile&utm_medium=android_app",
            "image": "team/junaid.png",
        },
        {
            "name": "Syed Khizar Hussain",
            "category": "Front End Developer",
            "linkedin_url": "https://www.linkedin.com/in/syed-khizar-95193b31b?utm_source=share&utm_campaign=share_via&utm_content=profile&utm_medium=android_app",
            "image": "team/khizar.png",
        },
        {
            "name": "Usama Zafar",
            "category": "AI Agents Automation Engineer",
            "linkedin_url": "https://www.linkedin.com/in/usamazafar41/",
            "image": "team/usama.png",
        },
    ]
    for member in team_data:
        TeamMember.objects.get_or_create(
            name=member["name"],
            defaults={
                "category":     member["category"],
                "linkedin_url": member["linkedin_url"],
                "image":        member["image"],
            },
        )

    # ── 2. Products ───────────────────────────────────────────────────────────
    product_data = [
        {
            "title": "Fuel Track Pro",
            "description": "Track your fuel consumption and save money with our intelligent fuel tracking system.",
            "image": "products/fuel.png",
            "link": "https://site-fuel-watch.lovable.app/",
        },
        {
            "title": "Rocket Attendance",
            "description": "Track your employee attendance and save time with our intelligent attendance tracking system.",
            "image": "products/attandence.png",
            "link": "https://rocketattendance.online/api/attendance/dashboard/",
        },
        {
            "title": "Dosta",
            "description": "Dosta UAE | Premium Vending and Catering Service Providers. Healthy food every day everywhere.",
            "image": "products/dosta.png",
            "link": "https://dosta.ae/",
        },
    ]
    for prod in product_data:
        Product.objects.get_or_create(
            title=prod["title"],
            defaults={
                "description": prod["description"],
                "image":       prod["image"],
                "link":        prod["link"],
            },
        )

    # ── 3. Services ───────────────────────────────────────────────────────────
    services_data = [
        {
            "slug":        "ai-development",
            "label":       "AI DEVELOPMENT",
            "title":       "AI Development Core Capabilities",
            "description": (
                "We deliver Custom AI model development including NLP, Computer Vision "
                "solutions, Predictive analytics, AI-powered chatbots, and Recommendation "
                "systems for measurable business impact."
            ),
            "features": [
                {
                    "title": "NLP & Computer Vision",
                    "description": "We deliver Custom AI model development including NLP, Computer Vision solutions, Predictive analytics, AI-powered chatbots, and Recommendation systems for business impact.",
                    "icon": "IconGlobal",
                },
                {
                    "title": "Predictive Analytics",
                    "description": "Harnessing historical and real-time data to forecast market trends, demand, and operational outcomes with high precision and reliability.",
                    "icon": "IconStacks",
                },
                {
                    "title": "AI-Powered Chatbots",
                    "description": "Deploying generative and conversational agents for 24/7 customer support, lead qualification, and internal workflow automation.",
                    "icon": "IconChart",
                },
                {
                    "title": "Recommendation Systems",
                    "description": "Building personalized engine platforms that maximize user engagement and conversion through smart product and content suggestions.",
                    "icon": "IconRefresh",
                },
            ],
        },
        {
            "slug":        "ai-agent-automation",
            "label":       "AGENT AUTOMATION",
            "title":       "Autonomous AI Agent Workflow Orchestration",
            "description": (
                "We automate workflows with intelligent RPA and Integration solutions, "
                "perfecting Document processing, Email automation, and Data entry "
                "automation for maximum operational efficiency."
            ),
            "features": [
                {
                    "title": "Robotic Process Automation (RPA)",
                    "description": "We automate workflows with intelligent RPA and Integration solutions, perfecting Document processing, Email automation, and Data entry automation for efficiency.",
                    "icon": "IconGlobal",
                },
                {
                    "title": "Workflow Optimization",
                    "description": "Designing streamlined, multi-step processes where autonomous agents reduce friction and decision latency across departments.",
                    "icon": "IconStacks",
                },
                {
                    "title": "Document Processing",
                    "description": "Agents capable of analyzing, extracting, and verifying complex information from unstructured documents at scale.",
                    "icon": "IconChart",
                },
                {
                    "title": "Integration Solutions",
                    "description": "Seamlessly connecting AI agents with existing enterprise systems (CRMs, ERPs) for real-time data exchange and task execution.",
                    "icon": "IconRefresh",
                },
            ],
        },
        {
            "slug":        "data-engineering",
            "label":       "DATA ENGINEERING",
            "title":       "Data Infrastructure & Pipeline Solutions",
            "description": (
                "We design robust Data pipeline development for Cloud data solutions, "
                "specialising in ETL/ELT, Data warehousing, Real-time processing, "
                "and comprehensive Data quality management."
            ),
            "features": [
                {
                    "title": "Data Pipelines & ETL/ELT",
                    "description": "We design robust Data pipeline development for Cloud data solutions. We specialize in ETL/ELT, Data warehousing, Real-time processing, and Data quality management.",
                    "icon": "IconGlobal",
                },
                {
                    "title": "Data Warehousing",
                    "description": "Building scalable, performant data warehouses (Snowflake, BigQuery) optimized for analytics, reporting, and large-scale ML training.",
                    "icon": "IconStacks",
                },
                {
                    "title": "Real-Time Processing",
                    "description": "Implementing streaming architectures (Kafka, Flink) to handle high-velocity data ingestion and low-latency decision-making.",
                    "icon": "IconChart",
                },
                {
                    "title": "Data Quality & Cloud Solutions",
                    "description": "Establishing comprehensive data quality management frameworks and deploying secure, cost-effective data solutions on major cloud providers.",
                    "icon": "IconRefresh",
                },
            ],
        },
        {
            "slug":        "machine-learning",
            "label":       "MACHINE LEARNING",
            "title":       "Applied Machine Learning Excellence",
            "description": (
                "We build Supervised and Unsupervised learning models including advanced "
                "Deep learning solutions, focusing on Time series forecasting, "
                "Classification & regression, and reliable MLOps deployment."
            ),
            "features": [
                {
                    "title": "Supervised & Unsupervised Models",
                    "description": "We build Supervised learning and Unsupervised learning including advanced Deep learning solutions, focusing on Time series forecasting, Classification & regression, and reliable Model deployment & monitoring.",
                    "icon": "IconGlobal",
                },
                {
                    "title": "Deep Learning Solutions",
                    "description": "Developing and optimizing neural networks for advanced tasks like image recognition, sequence generation, and complex pattern detection.",
                    "icon": "IconStacks",
                },
                {
                    "title": "Time Series & Forecasting",
                    "description": "Specialized models for analyzing time-dependent data to accurately predict future values, stock trends, and resource needs.",
                    "icon": "IconChart",
                },
                {
                    "title": "Model Deployment & Monitoring (ML Ops)",
                    "description": "Establishing MLOps pipelines for continuous integration, deployment, and performance monitoring of models in production environments.",
                    "icon": "IconRefresh",
                },
            ],
        },
    ]

    for s_data in services_data:
        service, _created = Service.objects.update_or_create(
            slug=s_data["slug"],
            defaults={
                "header_label": s_data["label"],
                "header_title": s_data["title"],
                "description":  s_data["description"],
            },
        )
        for f_data in s_data["features"]:
            ServiceFeature.objects.get_or_create(
                service=service,
                title=f_data["title"],
                defaults={
                    "description": f_data["description"],
                    "icon_name":   f_data["icon"],
                },
            )

    print("Seeding complete!")


if __name__ == "__main__":
    seed()
