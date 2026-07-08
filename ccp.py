from app import create_app, db
from app.models_learning import LearningPath, PathModule, ModuleSection

app = create_app()
with app.app_context():
    path = LearningPath.query.filter_by(slug='aws-cloud-practitioner').first()
    if not path:
        print('CCP path not found')
        exit()

    module = PathModule.query.filter_by(path_id=path.id, order_index=1).first()
    if not module:
        print('Module 1 not found')
        exit()

    # Update section 1
    s1 = ModuleSection.query.filter_by(module_id=module.id, order_index=1).first()
    if s1:
        s1.title = 'What is Cloud Computing?'
        s1.content = (
            '<p>Cloud computing is the on-demand delivery of computing services - including servers, storage, databases, networking, software, analytics, and intelligence - over the internet. Rather than owning and maintaining physical data centres and servers, organisations rent access to these resources from a cloud provider and pay only for what they use. This model fundamentally changes how businesses think about and consume IT infrastructure.</p>'
            '<p>Before cloud computing, businesses had to forecast their infrastructure needs months or even years in advance. If they underestimated, they faced capacity shortages during peak periods. If they overestimated, they wasted capital on idle hardware. Cloud computing eliminates this guesswork entirely by allowing resources to be provisioned in minutes and released just as quickly.</p>'
            '<h4>The Six Key Benefits of Cloud Computing</h4>'
            '<ul>'
            '<li><strong>Trade fixed expense for variable expense</strong> - Instead of investing heavily in data centres and servers before you know how you will use them, you pay only when you consume computing resources and pay only for how much you consume. This shifts IT spending from capital expenditure (CapEx) to operational expenditure (OpEx).</li>'
            '<li><strong>Benefit from massive economies of scale</strong> - Cloud providers aggregate usage from hundreds of thousands of customers, achieving far greater economies of scale than any individual organisation could. These savings are passed on to customers in the form of lower variable costs.</li>'
            '<li><strong>Stop guessing capacity</strong> - Eliminate guessing about your infrastructure capacity needs. When you make a capacity decision prior to deploying an application, you often end up either sitting on expensive idle resources or dealing with limited capacity. With cloud computing you can scale up or down within minutes, accessing as much or as little capacity as you need.</li>'
            '<li><strong>Increase speed and agility</strong> - New IT resources are only a click away. The time to make resources available to developers goes from weeks to minutes. This dramatically increases agility for the organisation since the cost and time it takes to experiment and develop is significantly lower.</li>'
            '<li><strong>Stop spending money running and maintaining data centres</strong> - Focus on projects that differentiate your business rather than the undifferentiated heavy lifting of racking, stacking, and powering physical servers. Cloud computing lets you focus on your own customers rather than the physical infrastructure.</li>'
            '<li><strong>Go global in minutes</strong> - Easily deploy your application in multiple regions around the world with just a few clicks. This means you can provide lower latency and a better experience for your customers at minimal cost.</li>'
            '</ul>'
            '<h4>Cloud Deployment Models</h4>'
            '<p>There are three primary ways organisations deploy cloud resources, and understanding the differences is critical for the exam.</p>'
            '<ul>'
            '<li><strong>Public Cloud</strong> - Resources are owned and operated by a third-party cloud provider and delivered over the internet. All hardware, software, and supporting infrastructure is owned and managed by the cloud provider. AWS, Microsoft Azure, and Google Cloud Platform (GCP) are public cloud providers. You share the underlying physical infrastructure with other customers but your data and workloads remain logically isolated.</li>'
            '<li><strong>Private Cloud</strong> - Cloud resources are used exclusively by a single organisation. A private cloud can be physically located at the organisation\'s on-site data centre or hosted by a third-party provider. The key distinction is that the services and infrastructure are always maintained on a private network and the hardware and software are dedicated solely to that organisation.</li>'
            '<li><strong>Hybrid Cloud</strong> - Hybrid clouds combine public and private clouds, bound together by technology that allows data and applications to be shared between them. This gives businesses greater flexibility, more deployment options, and allows them to optimise existing infrastructure, security, and compliance requirements. A common example is keeping sensitive customer data on a private cloud while running web-facing application tiers on the public cloud.</li>'
            '</ul>'
            '<h4>Why AWS Leads the Cloud Market</h4>'
            '<p>Amazon Web Services launched in 2006 and has maintained its position as the largest cloud provider globally with over 30% market share. AWS offers more than 200 fully featured services from data centres globally. Millions of customers - including the fastest growing startups, largest enterprises, and leading government agencies - trust AWS to power their infrastructure, become more agile, and lower costs. For South African learners in particular, AWS certification represents one of the most in-demand and globally recognised credentials in the ICT industry.</p>'
        )
        print('Section 1 updated')

    # Update section 2
    s2 = ModuleSection.query.filter_by(module_id=module.id, order_index=2).first()
    if s2:
        s2.title = 'AWS Global Infrastructure & Service Models'
        s2.content = (
            '<p>AWS operates one of the most extensive and reliable global cloud infrastructures in the world. Understanding how this infrastructure is organised is foundational knowledge for the Cloud Practitioner exam and for making sound architectural decisions in real-world projects.</p>'
            '<h4>Regions</h4>'
            '<p>An AWS Region is a physical location in the world where AWS clusters data centres. Each Region consists of a minimum of three, isolated, and physically separate Availability Zones within a geographic area. AWS currently operates over 30 geographic Regions worldwide, with ongoing expansion.</p>'
            '<p>When selecting a Region for your workloads, consider four key factors:</p>'
            '<ul>'
            '<li><strong>Data governance and legal requirements</strong> - Some countries require that certain types of data remain within their borders. For example, data subject to GDPR may need to remain within the European Union.</li>'
            '<li><strong>Proximity to customers</strong> - Deploying your application in the Region closest to your users reduces network latency and improves the user experience.</li>'
            '<li><strong>Service availability</strong> - Not all AWS services are available in every Region. New services typically launch in us-east-1 (Northern Virginia) first before expanding to other Regions.</li>'
            '<li><strong>Pricing</strong> - The cost of AWS services varies between Regions. us-east-1 is generally the most cost-effective Region due to economies of scale.</li>'
            '</ul>'
            '<h4>Availability Zones (AZs)</h4>'
            '<p>An Availability Zone is one or more discrete data centres with redundant power, networking, and connectivity within an AWS Region. AZs give customers the ability to operate production applications and databases that are more highly available, fault tolerant, and scalable than would be possible from a single data centre.</p>'
            '<p>Each AZ is physically separated from other AZs by a meaningful distance - typically tens of miles - but all AZs within a Region are interconnected with high-bandwidth, low-latency networking. This design means that a natural disaster, power outage, or other failure affecting one AZ is highly unlikely to affect other AZs in the same Region. Deploying applications across multiple AZs is one of the most fundamental best practices in AWS architecture.</p>'
            '<h4>Edge Locations and CloudFront</h4>'
            '<p>AWS CloudFront is a content delivery network (CDN) service that caches copies of your content at Edge Locations around the world. Edge Locations are data centre facilities that are separate from AWS Regions and exist solely to serve content to end users with the lowest possible latency. There are over 400 Edge Locations globally - significantly more than the number of Regions. When a user requests content, CloudFront routes the request to the Edge Location that provides the lowest latency, serving cached content directly from that edge point rather than fetching it from the origin server every time.</p>'
            '<h4>Cloud Service Models - IaaS, PaaS, and SaaS</h4>'
            '<p>Cloud services are broadly categorised into three models based on how much of the underlying stack the provider manages versus the customer.</p>'
            '<ul>'
            '<li><strong>Infrastructure as a Service (IaaS)</strong> - The cloud provider manages the physical hardware, hypervisor, and networking. You manage everything from the operating system upward - including the OS itself, middleware, runtime, data, and applications. IaaS gives you the most control and flexibility. Example: Amazon EC2.</li>'
            '<li><strong>Platform as a Service (PaaS)</strong> - The cloud provider manages the infrastructure AND the underlying platform components including the OS, middleware, and runtime. You focus only on deploying and managing your applications and data. Example: AWS Elastic Beanstalk automatically handles deployment, capacity provisioning, load balancing, and auto-scaling for your application code.</li>'
            '<li><strong>Software as a Service (SaaS)</strong> - The cloud provider manages everything. You simply use the software through a web browser or API. Example: Gmail, Salesforce, Amazon WorkMail.</li>'
            '</ul>'
            '<h4>The AWS Shared Responsibility Model</h4>'
            '<p>The Shared Responsibility Model is one of the most tested concepts in the Cloud Practitioner exam. It defines who is responsible for security and compliance in the AWS environment.</p>'
            '<p><strong>AWS is responsible for security "OF" the cloud</strong> - this includes the physical security of data centres, the hardware, the global network infrastructure, and the managed services layer.</p>'
            '<p><strong>You are responsible for security "IN" the cloud</strong> - this includes your data, identity and access management (IAM configurations), operating system patches on EC2 instances, network and firewall configuration within your VPC, and client-side and server-side encryption of your data.</p>'
        )
        print('Section 2 updated')

    # Add video section if it does not already exist
    existing_video = ModuleSection.query.filter_by(module_id=module.id, order_index=4).first()
    if not existing_video:
        video_section = ModuleSection(
            module_id=module.id,
            title='Full Course Video - Andrew Brown (14 Hours)',
            content=(
                '<p>This free 14-hour course by Andrew Brown of ExamPro covers the full AWS Certified Cloud Practitioner syllabus. It is one of the most comprehensive and highly rated free study resources available. Watch it alongside the reading material in this path to build a complete understanding before attempting the exam.</p>'
                '<div style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;border-radius:12px;margin:1.5rem 0;">'
                '<iframe style="position:absolute;top:0;left:0;width:100%;height:100%;border:0;border-radius:12px;" '
                'src="https://www.youtube.com/embed/7HKot-brXFE" '
                'title="AWS Certified Cloud Practitioner - Full Course by Andrew Brown" '
                'allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" '
                'allowfullscreen></iframe>'
                '</div>'
                '<p style="margin-top:1rem;"><strong>Duration:</strong> 14 hours | <strong>Instructor:</strong> Andrew Brown, ExamPro | <strong>Level:</strong> Beginner</p>'
                '<p>Use the YouTube chapters to navigate directly to specific topics as you work through each module in this learning path. After completing the video, return here and take each module quiz to test your understanding.</p>'
            ),
            order_index=4,
            section_type='video'
        )
        db.session.add(video_section)
        print('Video section added')
    else:
        print('Video section already exists')

    db.session.commit()
    print('Migration complete')
