from datetime import datetime
from app import db


class LearningPath(db.Model):
    __tablename__ = 'learning_path'
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(50), unique=True, nullable=False)  # e.g. 'aws-cloud-practitioner'
    title = db.Column(db.String(200), nullable=False)
    subtitle = db.Column(db.String(300))
    description = db.Column(db.Text)
    icon = db.Column(db.String(10))  # emoji
    color_primary = db.Column(db.String(7), default='#FF9900')
    color_secondary = db.Column(db.String(7), default='#232F3E')
    total_points = db.Column(db.Integer, default=0)
    estimated_hours = db.Column(db.Integer, default=40)
    difficulty = db.Column(db.String(20), default='Beginner')
    cert_provider = db.Column(db.String(100))   # "Amazon Web Services" etc.
    modules = db.relationship('PathModule', backref='path', lazy=True, order_by='PathModule.order_index')

    def __repr__(self):
        return f'<LearningPath {self.slug}>'


class PathModule(db.Model):
    __tablename__ = 'path_module'
    id = db.Column(db.Integer, primary_key=True)
    path_id = db.Column(db.Integer, db.ForeignKey('learning_path.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    order_index = db.Column(db.Integer, default=0)
    points = db.Column(db.Integer, default=50)
    icon = db.Column(db.String(10))
    sections = db.relationship('ModuleSection', backref='module', lazy=True, order_by='ModuleSection.order_index')
    quiz_questions = db.relationship('QuizQuestion', backref='module', lazy=True)

    def __repr__(self):
        return f'<PathModule {self.title}>'


class ModuleSection(db.Model):
    __tablename__ = 'module_section'
    id = db.Column(db.Integer, primary_key=True)
    module_id = db.Column(db.Integer, db.ForeignKey('path_module.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)   # HTML-safe educational text
    order_index = db.Column(db.Integer, default=0)
    section_type = db.Column(db.String(20), default='lesson')  # 'lesson', 'lab', 'video'

    def __repr__(self):
        return f'<ModuleSection {self.title}>'


class QuizQuestion(db.Model):
    __tablename__ = 'quiz_question'
    id = db.Column(db.Integer, primary_key=True)
    module_id = db.Column(db.Integer, db.ForeignKey('path_module.id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(300), nullable=False)
    option_b = db.Column(db.String(300), nullable=False)
    option_c = db.Column(db.String(300), nullable=False)
    option_d = db.Column(db.String(300), nullable=False)
    correct_answer = db.Column(db.String(1), nullable=False)  # 'A', 'B', 'C', 'D'
    explanation = db.Column(db.Text)
    difficulty = db.Column(db.String(20), default='medium')

    def __repr__(self):
        return f'<QuizQuestion {self.id}>'


class UserPathProgress(db.Model):
    __tablename__ = 'user_path_progress'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    path_id = db.Column(db.Integer, db.ForeignKey('learning_path.id'), nullable=False)
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    total_points_earned = db.Column(db.Integer, default=0)
    current_module_id = db.Column(db.Integer, db.ForeignKey('path_module.id'), nullable=True)

    user = db.relationship('User', backref=db.backref('path_progress', lazy=True))
    path = db.relationship('LearningPath', backref=db.backref('enrollments', lazy=True))

    __table_args__ = (db.UniqueConstraint('user_id', 'path_id'),)

    def __repr__(self):
        return f'<UserPathProgress user={self.user_id} path={self.path_id}>'


class UserModuleProgress(db.Model):
    __tablename__ = 'user_module_progress'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    module_id = db.Column(db.Integer, db.ForeignKey('path_module.id'), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    quiz_score = db.Column(db.Integer, nullable=True)        # percentage 0-100
    quiz_passed = db.Column(db.Boolean, default=False)
    quiz_attempts = db.Column(db.Integer, default=0)
    points_earned = db.Column(db.Integer, default=0)

    user = db.relationship('User', backref=db.backref('module_progress', lazy=True))
    module = db.relationship('PathModule', backref=db.backref('user_progress', lazy=True))

    __table_args__ = (db.UniqueConstraint('user_id', 'module_id'),)

    def __repr__(self):
        return f'<UserModuleProgress user={self.user_id} module={self.module_id}>'


class Certificate(db.Model):
    __tablename__ = 'certificate'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    path_id = db.Column(db.Integer, db.ForeignKey('learning_path.id'), nullable=False)
    cert_code = db.Column(db.String(20), unique=True, nullable=False)
    issued_at = db.Column(db.DateTime, default=datetime.utcnow)
    recipient_full_name = db.Column(db.String(200), nullable=False)
    total_points = db.Column(db.Integer, default=0)

    user = db.relationship('User', backref=db.backref('certificates', lazy=True))
    path = db.relationship('LearningPath', backref=db.backref('certificates', lazy=True))

    def __repr__(self):
        return f'<Certificate {self.cert_code}>'


# ─────────────────────────────────────────────────────────────────────────────
# Seed Data
# ─────────────────────────────────────────────────────────────────────────────

def seed_learning_paths():
    if LearningPath.query.count() > 0:
        return  # already seeded

    # ── AWS Cloud Practitioner ──────────────────────────────────────────────
    aws_path = LearningPath(
        slug='aws-cloud-practitioner',
        title='AWS Cloud Practitioner',
        subtitle='Foundational Cloud Certification',
        description=(
            'Build a solid foundation in cloud computing and AWS services. '
            'Covers cloud concepts, security, technology, and billing & pricing. '
            'Prepare for the AWS Certified Cloud Practitioner exam.'
        ),
        icon='☁️',
        color_primary='#FF9900',
        color_secondary='#232F3E',
        total_points=500,
        estimated_hours=40,
        difficulty='Beginner',
        cert_provider='AWS Learning Platform'
    )
    db.session.add(aws_path)
    db.session.flush()

    aws_modules = [
        {
            'title': 'Cloud Concepts & Computing Fundamentals',
            'description': 'Understand what cloud computing is, its benefits, and the AWS global infrastructure.',
            'order_index': 1,
            'points': 75,
            'icon': '🌐',
            'sections': [
                {
                    'title': 'What is Cloud Computing?',
                    'content': (
                        '<p>Cloud computing delivers computing services-servers, storage, databases, networking, software-'
                        'over the internet ("the cloud"). Instead of owning physical data centres, you rent access from '
                        'a cloud provider and pay only for what you use.</p>'
                        '<h4>Key Benefits</h4>'
                        '<ul>'
                        '<li><strong>Trade fixed expense for variable expense</strong> - pay only for what you consume.</li>'
                        '<li><strong>Benefit from massive economies of scale</strong> - providers aggregate usage from '
                        'hundreds of thousands of customers.</li>'
                        '<li><strong>Stop guessing capacity</strong> - scale up or down within minutes.</li>'
                        '<li><strong>Increase speed and agility</strong> - new resources available in seconds.</li>'
                        '<li><strong>Go global in minutes</strong> - deploy in multiple regions around the world.</li>'
                        '</ul>'
                        '<h4>Cloud Deployment Models</h4>'
                        '<ul>'
                        '<li><strong>Public Cloud</strong> - Resources owned and operated by a third-party provider, '
                        'delivered over the internet (e.g., AWS, Azure, GCP).</li>'
                        '<li><strong>Private Cloud</strong> - Cloud resources used exclusively by a single organisation, '
                        'hosted on-premises or by a third party.</li>'
                        '<li><strong>Hybrid Cloud</strong> - Combines public and private clouds, allowing data and '
                        'applications to be shared between them.</li>'
                        '</ul>'
                    ),
                    'order_index': 1,
                    'section_type': 'lesson'
                },
                {
                    'title': 'AWS Global Infrastructure',
                    'content': (
                        '<p>AWS operates a global infrastructure spanning <strong>Regions</strong>, '
                        '<strong>Availability Zones (AZs)</strong>, and <strong>Edge Locations</strong>.</p>'
                        '<h4>Regions</h4>'
                        '<p>A Region is a physical location in the world containing multiple, isolated data centres '
                        'called Availability Zones. Each Region is completely independent. When selecting a Region '
                        'consider: data governance/legal requirements, proximity to customers, service availability, '
                        'and pricing.</p>'
                        '<h4>Availability Zones</h4>'
                        '<p>An AZ is one or more discrete data centres with redundant power, networking, and '
                        'connectivity within a Region. AZs are physically separated-typically tens of miles apart-'
                        'to protect against disasters, while remaining close enough for low-latency replication. '
                        'Deploying across multiple AZs gives high availability.</p>'
                        '<h4>Edge Locations</h4>'
                        '<p>AWS CloudFront edge locations cache content closer to end users to reduce latency. '
                        'There are many more edge locations than Regions. AWS Local Zones extend AWS infrastructure '
                        'to more geographic locations for applications that require single-digit millisecond latency.</p>'
                    ),
                    'order_index': 2,
                    'section_type': 'lesson'
                },
                {
                    'title': 'Cloud Service Models',
                    'content': (
                        '<h4>Infrastructure as a Service (IaaS)</h4>'
                        '<p>Provides virtualised computing resources over the internet. You manage: OS, middleware, '
                        'runtime, data, applications. Provider manages: virtualisation, servers, storage, networking. '
                        'Example: Amazon EC2.</p>'
                        '<h4>Platform as a Service (PaaS)</h4>'
                        '<p>Provides a platform allowing customers to develop, run, and manage applications without '
                        'the complexity of building and maintaining the underlying infrastructure. Example: AWS Elastic '
                        'Beanstalk, AWS Lambda.</p>'
                        '<h4>Software as a Service (SaaS)</h4>'
                        '<p>Delivers software applications over the internet, on demand and typically on a subscription '
                        'basis. Provider manages everything. Example: Amazon WorkMail, Salesforce.</p>'
                        '<h4>Shared Responsibility Model</h4>'
                        '<p>AWS is responsible for security <em>of</em> the cloud (physical hardware, global '
                        'infrastructure, managed services). You are responsible for security <em>in</em> the cloud '
                        '(data, IAM, OS patches, network/firewall configuration, client-side encryption).</p>'
                    ),
                    'order_index': 3,
                    'section_type': 'lesson'
                }
            ],
            'questions': [
                {
                    'question_text': 'Which AWS concept refers to multiple, isolated locations within a Region, each with redundant power and networking?',
                    'option_a': 'Edge Locations',
                    'option_b': 'Availability Zones',
                    'option_c': 'Data Centres',
                    'option_d': 'Local Zones',
                    'correct_answer': 'B',
                    'explanation': 'Availability Zones (AZs) are discrete data centres within a Region designed to be isolated from failures in other AZs while remaining close enough for low-latency replication.'
                },
                {
                    'question_text': 'Which cloud computing benefit allows you to avoid estimating infrastructure needs months in advance?',
                    'option_a': 'Trade fixed expense for variable expense',
                    'option_b': 'Benefit from massive economies of scale',
                    'option_c': 'Stop guessing capacity',
                    'option_d': 'Increase agility',
                    'correct_answer': 'C',
                    'explanation': '"Stop guessing capacity" means you can scale up or down in minutes rather than planning months ahead.'
                },
                {
                    'question_text': 'Under the AWS Shared Responsibility Model, which of the following is the CUSTOMER\'S responsibility?',
                    'option_a': 'Physical security of data centres',
                    'option_b': 'Patching the hypervisor',
                    'option_c': 'Encrypting customer data stored in S3',
                    'option_d': 'Managing the global network infrastructure',
                    'correct_answer': 'C',
                    'explanation': 'Data encryption and access control for your own data is your responsibility ("security in the cloud"). Physical infrastructure is AWS\'s responsibility ("security of the cloud").'
                },
                {
                    'question_text': 'A company wants to run its application on AWS but also keep some workloads on-premises. Which deployment model best describes this?',
                    'option_a': 'Public Cloud',
                    'option_b': 'Private Cloud',
                    'option_c': 'Community Cloud',
                    'option_d': 'Hybrid Cloud',
                    'correct_answer': 'D',
                    'explanation': 'A Hybrid Cloud combines on-premises (private) infrastructure with public cloud resources, allowing data and apps to be shared between them.'
                },
                {
                    'question_text': 'Which AWS service model gives you the most control over the operating system and installed software?',
                    'option_a': 'Software as a Service (SaaS)',
                    'option_b': 'Platform as a Service (PaaS)',
                    'option_c': 'Infrastructure as a Service (IaaS)',
                    'option_d': 'Function as a Service (FaaS)',
                    'correct_answer': 'C',
                    'explanation': 'IaaS provides virtualised compute, storage, and networking. You manage the OS, middleware, and applications - giving you the most control.'
                }
            ]
        },
        {
            'title': 'Core AWS Services',
            'description': 'Explore key services: EC2, S3, RDS, VPC, Lambda, and IAM.',
            'order_index': 2,
            'points': 100,
            'icon': '⚙️',
            'sections': [
                {
                    'title': 'Amazon EC2 - Elastic Compute Cloud',
                    'content': (
                        '<p>Amazon EC2 provides resizable compute capacity in the cloud. It reduces the time '
                        'required to obtain and boot new server instances to minutes.</p>'
                        '<h4>Instance Types</h4>'
                        '<ul>'
                        '<li><strong>General Purpose</strong> (e.g., t3, m6i) - balanced compute, memory, networking.</li>'
                        '<li><strong>Compute Optimised</strong> (e.g., c6i) - high-performance processors; batch workloads.</li>'
                        '<li><strong>Memory Optimised</strong> (e.g., r6i) - fast performance for large in-memory datasets.</li>'
                        '<li><strong>Storage Optimised</strong> (e.g., i3) - high sequential read/write access to large datasets.</li>'
                        '</ul>'
                        '<h4>Purchasing Options</h4>'
                        '<ul>'
                        '<li><strong>On-Demand</strong> - pay by the second, no commitments.</li>'
                        '<li><strong>Reserved Instances</strong> - 1 or 3 year commitment, up to 72% savings.</li>'
                        '<li><strong>Spot Instances</strong> - bid on unused capacity, up to 90% savings (can be interrupted).</li>'
                        '<li><strong>Savings Plans</strong> - flexible pricing model, commit to a consistent usage amount.</li>'
                        '</ul>'
                    ),
                    'order_index': 1,
                    'section_type': 'lesson'
                },
                {
                    'title': 'Amazon S3 - Simple Storage Service',
                    'content': (
                        '<p>Amazon S3 is object storage built to store and retrieve any amount of data from '
                        'anywhere. It provides 99.999999999% (11 nines) durability.</p>'
                        '<h4>Storage Classes</h4>'
                        '<ul>'
                        '<li><strong>S3 Standard</strong> - frequently accessed data; low latency.</li>'
                        '<li><strong>S3 Standard-IA</strong> - infrequent access; lower cost, retrieval fee applies.</li>'
                        '<li><strong>S3 One Zone-IA</strong> - stored in single AZ; 20% cheaper than Standard-IA.</li>'
                        '<li><strong>S3 Glacier Instant Retrieval</strong> - archived data with millisecond retrieval.</li>'
                        '<li><strong>S3 Glacier Flexible Retrieval</strong> - minutes-to-hours retrieval; very low cost.</li>'
                        '<li><strong>S3 Glacier Deep Archive</strong> - lowest cost; 12-hour retrieval; long-term archive.</li>'
                        '</ul>'
                        '<h4>Key Concepts</h4>'
                        '<ul>'
                        '<li><strong>Buckets</strong> - containers for objects; globally unique names.</li>'
                        '<li><strong>Objects</strong> - files plus metadata; up to 5 TB each.</li>'
                        '<li><strong>Bucket Policies & ACLs</strong> - control access at bucket and object level.</li>'
                        '<li><strong>Versioning</strong> - keep multiple variants of an object in the same bucket.</li>'
                        '</ul>'
                    ),
                    'order_index': 2,
                    'section_type': 'lesson'
                },
                {
                    'title': 'IAM, VPC, RDS & Lambda',
                    'content': (
                        '<h4>AWS IAM - Identity and Access Management</h4>'
                        '<p>IAM lets you manage access to AWS services and resources. Key components: '
                        '<strong>Users</strong> (individual people/services), <strong>Groups</strong> (collection of users), '
                        '<strong>Roles</strong> (assumed by services/users for temporary access), '
                        '<strong>Policies</strong> (JSON documents defining permissions). '
                        'Best practice: grant least privilege.</p>'
                        '<h4>Amazon VPC - Virtual Private Cloud</h4>'
                        '<p>VPC lets you provision a logically isolated section of AWS Cloud. Key components: '
                        '<strong>Subnets</strong> (public/private), <strong>Route Tables</strong>, '
                        '<strong>Internet Gateway</strong> (connect VPC to internet), '
                        '<strong>NAT Gateway</strong> (allow private subnet instances to access internet), '
                        '<strong>Security Groups</strong> (stateful instance-level firewall), '
                        '<strong>Network ACLs</strong> (stateless subnet-level firewall).</p>'
                        '<h4>Amazon RDS - Relational Database Service</h4>'
                        '<p>Managed relational database service supporting MySQL, PostgreSQL, MariaDB, Oracle, '
                        'SQL Server, and Amazon Aurora. Handles: provisioning, patching, backup, recovery, '
                        'failover, and scaling.</p>'
                        '<h4>AWS Lambda</h4>'
                        '<p>Serverless compute - run code without provisioning or managing servers. Pay only '
                        'for compute time consumed. Automatically scales. Supports Node.js, Python, Java, Go, '
                        '.NET, Ruby, and custom runtimes.</p>'
                    ),
                    'order_index': 3,
                    'section_type': 'lesson'
                }
            ],
            'questions': [
                {
                    'question_text': 'Which EC2 purchasing option provides the GREATEST cost savings but can be interrupted by AWS with short notice?',
                    'option_a': 'On-Demand Instances',
                    'option_b': 'Reserved Instances',
                    'option_c': 'Spot Instances',
                    'option_d': 'Dedicated Hosts',
                    'correct_answer': 'C',
                    'explanation': 'Spot Instances use spare EC2 capacity and can save up to 90% versus On-Demand, but AWS can reclaim them with a 2-minute warning when capacity is needed.'
                },
                {
                    'question_text': 'Which S3 storage class is the most cost-effective for data that must be retained for 7+ years and is rarely, if ever, accessed?',
                    'option_a': 'S3 Standard',
                    'option_b': 'S3 Standard-IA',
                    'option_c': 'S3 Glacier Instant Retrieval',
                    'option_d': 'S3 Glacier Deep Archive',
                    'correct_answer': 'D',
                    'explanation': 'S3 Glacier Deep Archive is the lowest-cost storage class, designed for long-term retention (7-10 years) with retrieval times of 12 hours.'
                },
                {
                    'question_text': 'A developer needs their EC2 instance to read objects from an S3 bucket securely. What is the BEST practice?',
                    'option_a': 'Embed AWS access keys in the application code',
                    'option_b': 'Store credentials in an environment variable on the instance',
                    'option_c': 'Attach an IAM Role with appropriate S3 permissions to the EC2 instance',
                    'option_d': 'Create an IAM User and share the credentials via a config file',
                    'correct_answer': 'C',
                    'explanation': 'IAM Roles attached to EC2 instances provide temporary, automatically-rotated credentials - the best practice for granting AWS services access to other AWS services.'
                },
                {
                    'question_text': 'Which VPC component allows instances in a private subnet to initiate outbound internet traffic while preventing inbound connections from the internet?',
                    'option_a': 'Internet Gateway',
                    'option_b': 'NAT Gateway',
                    'option_c': 'VPC Peering',
                    'option_d': 'VPN Gateway',
                    'correct_answer': 'B',
                    'explanation': 'A NAT (Network Address Translation) Gateway allows outbound internet traffic from private subnets while blocking unsolicited inbound traffic.'
                },
                {
                    'question_text': 'Which AWS service runs your code in response to events and automatically manages the underlying compute resources?',
                    'option_a': 'Amazon EC2',
                    'option_b': 'Amazon ECS',
                    'option_c': 'AWS Lambda',
                    'option_d': 'AWS Fargate',
                    'correct_answer': 'C',
                    'explanation': 'AWS Lambda is a serverless compute service that runs code in response to triggers (events) and automatically provisions and scales the execution environment.'
                }
            ]
        },
        {
            'title': 'Cloud Security & Compliance',
            'description': 'Master IAM best practices, encryption, compliance programmes, and AWS security tools.',
            'order_index': 3,
            'points': 100,
            'icon': '🔒',
            'sections': [
                {
                    'title': 'IAM Best Practices & Multi-Factor Authentication',
                    'content': (
                        '<h4>IAM Best Practices</h4>'
                        '<ul>'
                        '<li>Lock away your AWS account root user access keys.</li>'
                        '<li>Create individual IAM users - never share credentials.</li>'
                        '<li>Use groups to assign permissions to IAM users.</li>'
                        '<li>Grant least privilege - only permissions required to perform a task.</li>'
                        '<li>Get started with AWS managed policies, move toward customer managed policies.</li>'
                        '<li>Rotate credentials regularly.</li>'
                        '<li>Remove unnecessary credentials.</li>'
                        '<li>Use policy conditions for extra security.</li>'
                        '<li>Monitor activity in your AWS account via AWS CloudTrail.</li>'
                        '</ul>'
                        '<h4>Multi-Factor Authentication (MFA)</h4>'
                        '<p>MFA adds an extra layer of protection on top of a username and password. '
                        'Enable MFA for the root account and all privileged IAM users. Supported MFA types: '
                        'Virtual MFA (Google Authenticator), Hardware MFA (YubiKey), SMS text (legacy).</p>'
                    ),
                    'order_index': 1,
                    'section_type': 'lesson'
                },
                {
                    'title': 'Encryption & Data Protection',
                    'content': (
                        '<h4>Encryption at Rest</h4>'
                        '<p>AWS services support encrypting stored data using keys managed by '
                        '<strong>AWS Key Management Service (KMS)</strong> or customer-provided keys. '
                        'Examples: EBS volume encryption, S3 server-side encryption (SSE-S3, SSE-KMS, SSE-C), '
                        'RDS encryption at rest.</p>'
                        '<h4>Encryption in Transit</h4>'
                        '<p>Use TLS/HTTPS to encrypt data moving between clients and AWS services. '
                        'AWS Certificate Manager (ACM) provisions and manages SSL/TLS certificates for free.</p>'
                        '<h4>AWS Shield & WAF</h4>'
                        '<ul>'
                        '<li><strong>AWS Shield Standard</strong> - automatically protects all AWS customers from '
                        'common DDoS attacks at no additional charge.</li>'
                        '<li><strong>AWS Shield Advanced</strong> - enhanced DDoS protection, 24/7 DDoS Response Team, '
                        'cost protection against scaling charges.</li>'
                        '<li><strong>AWS WAF</strong> - Web Application Firewall to protect against common web exploits '
                        '(SQL injection, XSS) using configurable rules.</li>'
                        '</ul>'
                    ),
                    'order_index': 2,
                    'section_type': 'lesson'
                },
                {
                    'title': 'Compliance & Governance',
                    'content': (
                        '<h4>AWS Compliance Programmes</h4>'
                        '<p>AWS maintains compliance with major programmes including: PCI DSS, HIPAA, SOC 1/2/3, '
                        'ISO 27001, FedRAMP, GDPR. Use <strong>AWS Artifact</strong> to download compliance reports '
                        'and agreements on demand.</p>'
                        '<h4>AWS Trusted Advisor</h4>'
                        '<p>Provides real-time guidance across five pillars: Cost Optimisation, Performance, '
                        'Security, Fault Tolerance, and Service Limits. Some checks are free; full access requires '
                        'Business or Enterprise Support.</p>'
                        '<h4>AWS Config</h4>'
                        '<p>Continuously monitors and records your AWS resource configurations and allows you to '
                        'automate evaluation of recorded configurations against desired configurations (compliance rules).</p>'
                        '<h4>AWS CloudTrail</h4>'
                        '<p>Records API calls made in your AWS account. Provides governance, compliance, and operational '
                        'and risk auditing. Logs are stored in S3. Essential for security investigation and auditing.</p>'
                    ),
                    'order_index': 3,
                    'section_type': 'lesson'
                }
            ],
            'questions': [
                {
                    'question_text': 'Which AWS service allows you to audit all API calls made within your AWS account?',
                    'option_a': 'AWS Config',
                    'option_b': 'Amazon CloudWatch',
                    'option_c': 'AWS CloudTrail',
                    'option_d': 'AWS Trusted Advisor',
                    'correct_answer': 'C',
                    'explanation': 'AWS CloudTrail records every API call in your account, enabling governance, compliance, and operational and risk auditing.'
                },
                {
                    'question_text': 'A company must protect its web application from SQL injection attacks. Which AWS service should they use?',
                    'option_a': 'AWS Shield Standard',
                    'option_b': 'AWS WAF',
                    'option_c': 'Amazon Inspector',
                    'option_d': 'AWS GuardDuty',
                    'correct_answer': 'B',
                    'explanation': 'AWS WAF (Web Application Firewall) allows you to create rules to block common web exploits including SQL injection and cross-site scripting (XSS).'
                },
                {
                    'question_text': 'Where can you download AWS compliance reports such as SOC 2 and PCI DSS?',
                    'option_a': 'AWS Trusted Advisor',
                    'option_b': 'AWS Security Hub',
                    'option_c': 'AWS Artifact',
                    'option_d': 'AWS Config',
                    'correct_answer': 'C',
                    'explanation': 'AWS Artifact is a self-service portal for on-demand access to AWS compliance documentation and AWS agreements.'
                },
                {
                    'question_text': 'Which is an IAM security best practice?',
                    'option_a': 'Share the root account credentials with senior administrators',
                    'option_b': 'Grant all permissions to simplify management',
                    'option_c': 'Use a single IAM user account shared across the team',
                    'option_d': 'Enable MFA for the root account and privileged users',
                    'correct_answer': 'D',
                    'explanation': 'Enabling MFA for the root account and all privileged users is a critical IAM security best practice. The root account should never be shared.'
                },
                {
                    'question_text': 'Which AWS managed service uses machine learning to continuously monitor for malicious activity and unauthorised behaviour in your account?',
                    'option_a': 'Amazon Inspector',
                    'option_b': 'AWS GuardDuty',
                    'option_c': 'AWS Security Hub',
                    'option_d': 'Amazon Macie',
                    'correct_answer': 'B',
                    'explanation': 'Amazon GuardDuty is a threat detection service that continuously monitors your AWS accounts and workloads for malicious activity and delivers detailed security findings.'
                }
            ]
        },
        {
            'title': 'Pricing, Billing & Support',
            'description': 'Understand AWS pricing models, cost management tools, and support plans.',
            'order_index': 4,
            'points': 75,
            'icon': '💰',
            'sections': [
                {
                    'title': 'AWS Pricing Fundamentals',
                    'content': (
                        '<h4>AWS Pricing Principles</h4>'
                        '<p>AWS pricing follows three fundamental characteristics:</p>'
                        '<ul>'
                        '<li><strong>Pay as you go</strong> - pay for exactly what you use, when you use it.</li>'
                        '<li><strong>Pay less when you reserve</strong> - Reserved Instances and Savings Plans offer '
                        'significant discounts in exchange for a commitment.</li>'
                        '<li><strong>Pay less with volume-based discounts</strong> - the more you use, the less you pay '
                        'per unit (e.g., S3 tiered pricing).</li>'
                        '</ul>'
                        '<h4>AWS Free Tier</h4>'
                        '<p>Three types of free tier offers:</p>'
                        '<ul>'
                        '<li><strong>Always Free</strong> - never expires (e.g., AWS Lambda: 1M requests/month).</li>'
                        '<li><strong>12 Months Free</strong> - available for 12 months from sign-up '
                        '(e.g., EC2 t2.micro 750 hrs/month, S3 5 GB).</li>'
                        '<li><strong>Trials</strong> - short-term free trials for specific services.</li>'
                        '</ul>'
                    ),
                    'order_index': 1,
                    'section_type': 'lesson'
                },
                {
                    'title': 'Cost Management Tools',
                    'content': (
                        '<h4>AWS Cost Explorer</h4>'
                        '<p>Visualise, understand, and manage your AWS costs and usage over time. View historical '
                        'data going back 13 months and forecast future costs.</p>'
                        '<h4>AWS Budgets</h4>'
                        '<p>Set custom budgets to track costs and usage and receive alerts when you exceed '
                        '(or are forecasted to exceed) your thresholds. Supports cost, usage, reservation, '
                        'and Savings Plans budgets.</p>'
                        '<h4>AWS Pricing Calculator</h4>'
                        '<p>Estimate the cost of your AWS use cases before you deploy. Create cost estimates for '
                        'architectures or individual services.</p>'
                        '<h4>AWS Cost and Usage Report (CUR)</h4>'
                        '<p>The most detailed available set of AWS cost and usage data. Delivered to S3 as CSV files.</p>'
                        '<h4>AWS Organisations & Consolidated Billing</h4>'
                        '<p>Combine usage across accounts in your organisation to qualify for volume pricing discounts. '
                        'One bill for all accounts. Master account pays for all member accounts.</p>'
                    ),
                    'order_index': 2,
                    'section_type': 'lesson'
                },
                {
                    'title': 'AWS Support Plans',
                    'content': (
                        '<h4>Support Plan Tiers</h4>'
                        '<table style="width:100%;border-collapse:collapse;font-size:0.9rem;">'
                        '<tr style="background:rgba(255,153,0,0.3);">'
                        '<th style="padding:8px;border:1px solid rgba(255,255,255,0.2);">Plan</th>'
                        '<th style="padding:8px;border:1px solid rgba(255,255,255,0.2);">Price</th>'
                        '<th style="padding:8px;border:1px solid rgba(255,255,255,0.2);">Best For</th>'
                        '</tr>'
                        '<tr><td style="padding:8px;border:1px solid rgba(255,255,255,0.2);">Basic</td>'
                        '<td style="padding:8px;border:1px solid rgba(255,255,255,0.2);">Free</td>'
                        '<td style="padding:8px;border:1px solid rgba(255,255,255,0.2);">All accounts; documentation, whitepapers, forums</td></tr>'
                        '<tr><td style="padding:8px;border:1px solid rgba(255,255,255,0.2);">Developer</td>'
                        '<td style="padding:8px;border:1px solid rgba(255,255,255,0.2);">$29+/mo</td>'
                        '<td style="padding:8px;border:1px solid rgba(255,255,255,0.2);">Experimenting; business hours email support</td></tr>'
                        '<tr><td style="padding:8px;border:1px solid rgba(255,255,255,0.2);">Business</td>'
                        '<td style="padding:8px;border:1px solid rgba(255,255,255,0.2);">$100+/mo</td>'
                        '<td style="padding:8px;border:1px solid rgba(255,255,255,0.2);">Production workloads; 24/7 phone, chat, email</td></tr>'
                        '<tr><td style="padding:8px;border:1px solid rgba(255,255,255,0.2);">Enterprise On-Ramp</td>'
                        '<td style="padding:8px;border:1px solid rgba(255,255,255,0.2);">$5,500+/mo</td>'
                        '<td style="padding:8px;border:1px solid rgba(255,255,255,0.2);">Business-critical workloads; TAM pool access</td></tr>'
                        '<tr><td style="padding:8px;border:1px solid rgba(255,255,255,0.2);">Enterprise</td>'
                        '<td style="padding:8px;border:1px solid rgba(255,255,255,0.2);">$15,000+/mo</td>'
                        '<td style="padding:8px;border:1px solid rgba(255,255,255,0.2);">Mission-critical; dedicated Technical Account Manager</td></tr>'
                        '</table>'
                    ),
                    'order_index': 3,
                    'section_type': 'lesson'
                }
            ],
            'questions': [
                {
                    'question_text': 'Which AWS Support plan provides access to a dedicated Technical Account Manager (TAM)?',
                    'option_a': 'Basic',
                    'option_b': 'Developer',
                    'option_c': 'Business',
                    'option_d': 'Enterprise',
                    'correct_answer': 'D',
                    'explanation': 'The Enterprise Support plan includes a dedicated Technical Account Manager (TAM) who provides proactive guidance and advocacy.'
                },
                {
                    'question_text': 'A company has multiple AWS accounts for different departments. Which feature allows them to receive a single bill and share volume pricing discounts?',
                    'option_a': 'AWS Cost Explorer',
                    'option_b': 'AWS Budgets',
                    'option_c': 'AWS Organisations Consolidated Billing',
                    'option_d': 'AWS Cost and Usage Report',
                    'correct_answer': 'C',
                    'explanation': 'AWS Organisations Consolidated Billing combines usage across all accounts so the organisation qualifies for volume pricing discounts and receives one bill.'
                },
                {
                    'question_text': 'Which tool helps you estimate the cost of a new AWS architecture BEFORE deploying it?',
                    'option_a': 'AWS Cost Explorer',
                    'option_b': 'AWS Budgets',
                    'option_c': 'AWS Pricing Calculator',
                    'option_d': 'AWS Cost and Usage Report',
                    'correct_answer': 'C',
                    'explanation': 'The AWS Pricing Calculator allows you to model your architecture and estimate monthly costs before any deployment.'
                },
                {
                    'question_text': 'Which of the following is an example of an "Always Free" AWS Free Tier offering?',
                    'option_a': '750 hours/month of t2.micro EC2 for 12 months',
                    'option_b': '5 GB of S3 storage for 12 months',
                    'option_c': '1 million AWS Lambda requests per month',
                    'option_d': '30 GB of Amazon EBS storage for 12 months',
                    'correct_answer': 'C',
                    'explanation': 'AWS Lambda\'s 1 million requests per month is an "Always Free" offer that never expires. The others (EC2, S3, EBS) are 12-Months Free offers.'
                },
                {
                    'question_text': 'Which AWS pricing principle offers the greatest discount in exchange for a 1 or 3 year commitment?',
                    'option_a': 'Pay as you go',
                    'option_b': 'Pay less when you reserve',
                    'option_c': 'Pay less with volume-based discounts',
                    'option_d': 'Pay per request',
                    'correct_answer': 'B',
                    'explanation': '"Pay less when you reserve" - Reserved Instances and Savings Plans offer up to 72% savings versus On-Demand in exchange for a 1 or 3 year commitment.'
                }
            ]
        },
        {
            'title': 'Architecture & Well-Architected Framework',
            'description': 'Learn the five pillars of the AWS Well-Architected Framework and design resilient systems.',
            'order_index': 5,
            'points': 75,
            'icon': '🏗️',
            'sections': [
                {
                    'title': 'The AWS Well-Architected Framework',
                    'content': (
                        '<p>The AWS Well-Architected Framework provides a consistent approach for customers and '
                        'partners to evaluate architectures, and implement designs that can scale over time.</p>'
                        '<h4>The Six Pillars</h4>'
                        '<ol>'
                        '<li><strong>Operational Excellence</strong> - ability to run and monitor systems to deliver business value. '
                        'Key practices: Infrastructure as Code (CloudFormation), CI/CD pipelines, small reversible changes.</li>'
                        '<li><strong>Security</strong> - protecting information and systems. '
                        'Key practices: implement a strong identity foundation, enable traceability, apply security at all layers, automate security best practices, protect data in transit and at rest.</li>'
                        '<li><strong>Reliability</strong> - ability to recover from failures and dynamically acquire resources. '
                        'Key practices: test recovery procedures, automatically recover from failure, scale horizontally.</li>'
                        '<li><strong>Performance Efficiency</strong> - using computing resources efficiently. '
                        'Key practices: use serverless architectures, experiment more often, go global in minutes.</li>'
                        '<li><strong>Cost Optimisation</strong> - avoiding unnecessary costs. '
                        'Key practices: adopt a consumption model, measure overall efficiency, stop spending on undifferentiated heavy lifting.</li>'
                        '<li><strong>Sustainability</strong> - minimising environmental impacts. '
                        'Key practices: understand your impact, maximise utilisation, use managed services.</li>'
                        '</ol>'
                    ),
                    'order_index': 1,
                    'section_type': 'lesson'
                },
                {
                    'title': 'High Availability & Fault Tolerance',
                    'content': (
                        '<h4>High Availability (HA)</h4>'
                        '<p>Systems designed to remain operational even if some components fail. '
                        'AWS services that enable HA: Elastic Load Balancing (ELB), Auto Scaling Groups (ASG), '
                        'Multi-AZ deployments (RDS, ElastiCache), Route 53 health checks and failover routing.</p>'
                        '<h4>Fault Tolerance vs High Availability</h4>'
                        '<ul>'
                        '<li><strong>Fault Tolerant</strong> - system continues to function even when components fail '
                        '(zero downtime); requires redundancy at every layer.</li>'
                        '<li><strong>Highly Available</strong> - system is designed to recover quickly from failure '
                        '(minimal downtime); uses redundancy but may have brief outages during failover.</li>'
                        '</ul>'
                        '<h4>Disaster Recovery Strategies</h4>'
                        '<ul>'
                        '<li><strong>Backup & Restore</strong> - cheapest; backup data to S3; longest RTO/RPO.</li>'
                        '<li><strong>Pilot Light</strong> - minimal version of environment always running; '
                        'scale up when needed.</li>'
                        '<li><strong>Warm Standby</strong> - scaled-down but fully functional version always running.</li>'
                        '<li><strong>Multi-Site Active/Active</strong> - most expensive; fastest recovery; '
                        'run at full capacity in multiple regions simultaneously.</li>'
                        '</ul>'
                    ),
                    'order_index': 2,
                    'section_type': 'lesson'
                }
            ],
            'questions': [
                {
                    'question_text': 'Which AWS Well-Architected Framework pillar focuses on protecting information and systems?',
                    'option_a': 'Reliability',
                    'option_b': 'Operational Excellence',
                    'option_c': 'Security',
                    'option_d': 'Cost Optimisation',
                    'correct_answer': 'C',
                    'explanation': 'The Security pillar focuses on protecting information, systems, and assets while delivering business value through risk assessments and mitigation strategies.'
                },
                {
                    'question_text': 'Which disaster recovery strategy has the lowest Recovery Time Objective (RTO) but also the highest cost?',
                    'option_a': 'Backup and Restore',
                    'option_b': 'Pilot Light',
                    'option_c': 'Warm Standby',
                    'option_d': 'Multi-Site Active/Active',
                    'correct_answer': 'D',
                    'explanation': 'Multi-Site Active/Active runs at full capacity in multiple regions simultaneously, offering near-zero RTO/RPO, but is the most expensive approach.'
                },
                {
                    'question_text': 'A company wants to automatically add more EC2 instances when CPU utilisation exceeds 70%. Which service enables this?',
                    'option_a': 'Elastic Load Balancing',
                    'option_b': 'Amazon CloudWatch',
                    'option_c': 'EC2 Auto Scaling',
                    'option_d': 'AWS Elastic Beanstalk',
                    'correct_answer': 'C',
                    'explanation': 'EC2 Auto Scaling automatically adjusts the number of EC2 instances in response to demand changes, scale policies, or scheduled actions.'
                },
                {
                    'question_text': 'Which pillar of the AWS Well-Architected Framework emphasises the ability to run workloads effectively and to gain insight into their operation?',
                    'option_a': 'Performance Efficiency',
                    'option_b': 'Operational Excellence',
                    'option_c': 'Reliability',
                    'option_d': 'Sustainability',
                    'correct_answer': 'B',
                    'explanation': 'Operational Excellence focuses on running workloads effectively, gaining insights through monitoring, and continuously improving processes and procedures.'
                },
                {
                    'question_text': 'What is the Well-Architected Framework pillar that involves running and monitoring systems to deliver business value?',
                    'option_a': 'Security',
                    'option_b': 'Cost Optimisation',
                    'option_c': 'Operational Excellence',
                    'option_d': 'Reliability',
                    'correct_answer': 'C',
                    'explanation': 'Operational Excellence is the pillar that includes the ability to run and monitor systems to deliver business value and to continually improve supporting processes and procedures.'
                }
            ]
        }
    ]

    for mod_data in aws_modules:
        mod = PathModule(
            path_id=aws_path.id,
            title=mod_data['title'],
            description=mod_data['description'],
            order_index=mod_data['order_index'],
            points=mod_data['points'],
            icon=mod_data['icon']
        )
        db.session.add(mod)
        db.session.flush()

        for sec in mod_data.get('sections', []):
            section = ModuleSection(
                module_id=mod.id,
                title=sec['title'],
                content=sec['content'],
                order_index=sec['order_index'],
                section_type=sec['section_type']
            )
            db.session.add(section)

        for q in mod_data.get('questions', []):
            question = QuizQuestion(
                module_id=mod.id,
                question_text=q['question_text'],
                option_a=q['option_a'],
                option_b=q['option_b'],
                option_c=q['option_c'],
                option_d=q['option_d'],
                correct_answer=q['correct_answer'],
                explanation=q.get('explanation', '')
            )
            db.session.add(question)

    # ── Cisco CCNA ──────────────────────────────────────────────────────────
    ccna_path = LearningPath(
        slug='cisco-ccna',
        title='Cisco CCNA',
        subtitle='Associate Network Certification',
        description=(
            'Build core networking skills covering IP addressing, switching, routing, '
            'network security, automation, and programmability. '
            'Prepare for the Cisco CCNA 200-301 exam.'
        ),
        icon='🌍',
        color_primary='#049fd9',
        color_secondary='#1a1a2e',
        total_points=500,
        estimated_hours=50,
        difficulty='Intermediate',
        cert_provider='AWS Learning Platform'
    )
    db.session.add(ccna_path)
    db.session.flush()

    ccna_modules = [
        {
            'title': 'Network Fundamentals',
            'description': 'OSI & TCP/IP models, network devices, cables, and basic topology.',
            'order_index': 1,
            'points': 75,
            'icon': '🔌',
            'sections': [
                {
                    'title': 'OSI & TCP/IP Reference Models',
                    'content': (
                        '<h4>The OSI Model (7 Layers)</h4>'
                        '<table style="width:100%;border-collapse:collapse;font-size:0.9rem;">'
                        '<tr style="background:rgba(4,159,217,0.3);">'
                        '<th style="padding:8px;border:1px solid rgba(255,255,255,0.2);">Layer</th>'
                        '<th style="padding:8px;border:1px solid rgba(255,255,255,0.2);">Name</th>'
                        '<th style="padding:8px;border:1px solid rgba(255,255,255,0.2);">Key Protocols/Devices</th>'
                        '</tr>'
                        '<tr><td style="padding:6px;border:1px solid rgba(255,255,255,0.2);">7</td>'
                        '<td style="padding:6px;border:1px solid rgba(255,255,255,0.2);">Application</td>'
                        '<td style="padding:6px;border:1px solid rgba(255,255,255,0.2);">HTTP, HTTPS, FTP, SMTP, DNS</td></tr>'
                        '<tr><td style="padding:6px;border:1px solid rgba(255,255,255,0.2);">6</td>'
                        '<td style="padding:6px;border:1px solid rgba(255,255,255,0.2);">Presentation</td>'
                        '<td style="padding:6px;border:1px solid rgba(255,255,255,0.2);">TLS, SSL, JPEG, ASCII</td></tr>'
                        '<tr><td style="padding:6px;border:1px solid rgba(255,255,255,0.2);">5</td>'
                        '<td style="padding:6px;border:1px solid rgba(255,255,255,0.2);">Session</td>'
                        '<td style="padding:6px;border:1px solid rgba(255,255,255,0.2);">NetBIOS, RPC</td></tr>'
                        '<tr><td style="padding:6px;border:1px solid rgba(255,255,255,0.2);">4</td>'
                        '<td style="padding:6px;border:1px solid rgba(255,255,255,0.2);">Transport</td>'
                        '<td style="padding:6px;border:1px solid rgba(255,255,255,0.2);">TCP, UDP; Segments</td></tr>'
                        '<tr><td style="padding:6px;border:1px solid rgba(255,255,255,0.2);">3</td>'
                        '<td style="padding:6px;border:1px solid rgba(255,255,255,0.2);">Network</td>'
                        '<td style="padding:6px;border:1px solid rgba(255,255,255,0.2);">IP, ICMP, Routers; Packets</td></tr>'
                        '<tr><td style="padding:6px;border:1px solid rgba(255,255,255,0.2);">2</td>'
                        '<td style="padding:6px;border:1px solid rgba(255,255,255,0.2);">Data Link</td>'
                        '<td style="padding:6px;border:1px solid rgba(255,255,255,0.2);">Ethernet, MAC; Switches; Frames</td></tr>'
                        '<tr><td style="padding:6px;border:1px solid rgba(255,255,255,0.2);">1</td>'
                        '<td style="padding:6px;border:1px solid rgba(255,255,255,0.2);">Physical</td>'
                        '<td style="padding:6px;border:1px solid rgba(255,255,255,0.2);">Cables, Hubs, Repeaters; Bits</td></tr>'
                        '</table>'
                        '<h4>TCP/IP Model (4 Layers)</h4>'
                        '<p>Application → Transport → Internet → Network Access. '
                        'Maps roughly to OSI layers 7-5, 4, 3, and 2-1 respectively.</p>'
                    ),
                    'order_index': 1,
                    'section_type': 'lesson'
                },
                {
                    'title': 'Network Devices & Topologies',
                    'content': (
                        '<h4>Key Network Devices</h4>'
                        '<ul>'
                        '<li><strong>Hub</strong> - Layer 1; broadcasts all frames to all ports; half-duplex; obsolete.</li>'
                        '<li><strong>Switch</strong> - Layer 2; learns MAC addresses; forwards frames only to the correct port; '
                        'full-duplex; creates separate collision domains per port.</li>'
                        '<li><strong>Router</strong> - Layer 3; routes packets between different networks using IP addresses; '
                        'separates broadcast domains.</li>'
                        '<li><strong>Firewall</strong> - inspects and filters traffic based on rules; can be stateful or stateless.</li>'
                        '<li><strong>Wireless Access Point (WAP)</strong> - connects wireless clients to a wired network.</li>'
                        '</ul>'
                        '<h4>Ethernet Cable Types</h4>'
                        '<ul>'
                        '<li><strong>Straight-through</strong> - connects different device types (PC to switch, switch to router).</li>'
                        '<li><strong>Crossover</strong> - connects same device types (PC to PC, switch to switch). '
                        'Modern switches use Auto-MDIX to detect automatically.</li>'
                        '<li><strong>Fibre Optic</strong> - uses light; immune to EMI; longer distances. '
                        'Single-mode for long distances; multi-mode for shorter distances.</li>'
                        '</ul>'
                        '<h4>Network Topologies</h4>'
                        '<ul>'
                        '<li><strong>Star</strong> - all devices connect to a central switch (most common in LANs).</li>'
                        '<li><strong>Bus</strong> - all devices share a single cable (legacy).</li>'
                        '<li><strong>Ring</strong> - devices connect in a loop; Token Ring (legacy).</li>'
                        '<li><strong>Mesh</strong> - every device connected to every other device; high redundancy.</li>'
                        '</ul>'
                    ),
                    'order_index': 2,
                    'section_type': 'lesson'
                }
            ],
            'questions': [
                {
                    'question_text': 'At which OSI layer do switches operate?',
                    'option_a': 'Layer 1 - Physical',
                    'option_b': 'Layer 2 - Data Link',
                    'option_c': 'Layer 3 - Network',
                    'option_d': 'Layer 4 - Transport',
                    'correct_answer': 'B',
                    'explanation': 'Switches operate at Layer 2 (Data Link) and use MAC addresses to make forwarding decisions, creating separate collision domains per port.'
                },
                {
                    'question_text': 'Which protocol operates at the Transport layer and provides reliable, connection-oriented delivery?',
                    'option_a': 'IP',
                    'option_b': 'UDP',
                    'option_c': 'TCP',
                    'option_d': 'ICMP',
                    'correct_answer': 'C',
                    'explanation': 'TCP (Transmission Control Protocol) operates at Layer 4 (Transport) and provides reliable, ordered, error-checked delivery with connection establishment and flow control.'
                },
                {
                    'question_text': 'Which cable type connects two devices of the SAME type, such as a switch to another switch?',
                    'option_a': 'Straight-through',
                    'option_b': 'Rollover (console)',
                    'option_c': 'Crossover',
                    'option_d': 'Single-mode fibre',
                    'correct_answer': 'C',
                    'explanation': 'Crossover cables are used to connect like devices (PC to PC, switch to switch). However, most modern devices support Auto-MDIX, which detects the cable type automatically.'
                },
                {
                    'question_text': 'What is the PDU (Protocol Data Unit) name at the Network layer (Layer 3)?',
                    'option_a': 'Bit',
                    'option_b': 'Frame',
                    'option_c': 'Packet',
                    'option_d': 'Segment',
                    'correct_answer': 'C',
                    'explanation': 'At Layer 3 (Network), the PDU is called a Packet. Layer 2 = Frame, Layer 4 = Segment, Layer 1 = Bit.'
                },
                {
                    'question_text': 'Which network device separates broadcast domains?',
                    'option_a': 'Hub',
                    'option_b': 'Bridge',
                    'option_c': 'Switch',
                    'option_d': 'Router',
                    'correct_answer': 'D',
                    'explanation': 'Routers operate at Layer 3 and separate broadcast domains. Switches separate collision domains but forward broadcasts to all ports within a VLAN.'
                }
            ]
        },
        {
            'title': 'IP Addressing & Subnetting',
            'description': 'Master IPv4/IPv6 addressing, CIDR notation, and subnetting calculations.',
            'order_index': 2,
            'points': 100,
            'icon': '📊',
            'sections': [
                {
                    'title': 'IPv4 Addressing',
                    'content': (
                        '<h4>IPv4 Basics</h4>'
                        '<p>An IPv4 address is a 32-bit number expressed in dotted-decimal notation '
                        '(e.g., 192.168.1.10). Divided into a <strong>network</strong> portion and a '
                        '<strong>host</strong> portion, determined by the subnet mask.</p>'
                        '<h4>IPv4 Address Classes (Classful)</h4>'
                        '<table style="width:100%;border-collapse:collapse;font-size:0.9rem;">'
                        '<tr style="background:rgba(4,159,217,0.3);">'
                        '<th style="padding:8px;border:1px solid rgba(255,255,255,0.2);">Class</th>'
                        '<th style="padding:8px;border:1px solid rgba(255,255,255,0.2);">Range</th>'
                        '<th style="padding:8px;border:1px solid rgba(255,255,255,0.2);">Default Mask</th>'
                        '<th style="padding:8px;border:1px solid rgba(255,255,255,0.2);">Use</th>'
                        '</tr>'
                        '<tr><td style="padding:6px;border:1px solid rgba(255,255,255,0.2);">A</td>'
                        '<td style="padding:6px;border:1px solid rgba(255,255,255,0.2);">1.0.0.0 - 126.255.255.255</td>'
                        '<td style="padding:6px;border:1px solid rgba(255,255,255,0.2);">/8 (255.0.0.0)</td>'
                        '<td style="padding:6px;border:1px solid rgba(255,255,255,0.2);">Large networks</td></tr>'
                        '<tr><td style="padding:6px;border:1px solid rgba(255,255,255,0.2);">B</td>'
                        '<td style="padding:6px;border:1px solid rgba(255,255,255,0.2);">128.0.0.0 - 191.255.255.255</td>'
                        '<td style="padding:6px;border:1px solid rgba(255,255,255,0.2);">/16 (255.255.0.0)</td>'
                        '<td style="padding:6px;border:1px solid rgba(255,255,255,0.2);">Medium networks</td></tr>'
                        '<tr><td style="padding:6px;border:1px solid rgba(255,255,255,0.2);">C</td>'
                        '<td style="padding:6px;border:1px solid rgba(255,255,255,0.2);">192.0.0.0 - 223.255.255.255</td>'
                        '<td style="padding:6px;border:1px solid rgba(255,255,255,0.2);">/24 (255.255.255.0)</td>'
                        '<td style="padding:6px;border:1px solid rgba(255,255,255,0.2);">Small networks (up to 254 hosts)</td></tr>'
                        '</table>'
                        '<h4>Private IP Ranges (RFC 1918)</h4>'
                        '<ul>'
                        '<li>10.0.0.0/8 - Class A private range</li>'
                        '<li>172.16.0.0/12 - Class B private range (172.16.0.0 - 172.31.255.255)</li>'
                        '<li>192.168.0.0/16 - Class C private range</li>'
                        '</ul>'
                    ),
                    'order_index': 1,
                    'section_type': 'lesson'
                },
                {
                    'title': 'CIDR & Subnetting',
                    'content': (
                        '<h4>CIDR Notation</h4>'
                        '<p>Classless Inter-Domain Routing (CIDR) uses a prefix length (e.g., /24) instead of '
                        'classful subnet masks. The prefix length specifies how many bits are the network portion.</p>'
                        '<h4>Subnetting Formula</h4>'
                        '<ul>'
                        '<li><strong>Number of subnets</strong> = 2<sup>s</sup> where s = subnet bits borrowed.</li>'
                        '<li><strong>Hosts per subnet</strong> = 2<sup>h</sup> - 2 where h = host bits '
                        '(subtract 2 for network address and broadcast).</li>'
                        '</ul>'
                        '<h4>Common Subnet Reference</h4>'
                        '<table style="width:100%;border-collapse:collapse;font-size:0.9rem;">'
                        '<tr style="background:rgba(4,159,217,0.3);">'
                        '<th style="padding:6px;border:1px solid rgba(255,255,255,0.2);">Prefix</th>'
                        '<th style="padding:6px;border:1px solid rgba(255,255,255,0.2);">Subnet Mask</th>'
                        '<th style="padding:6px;border:1px solid rgba(255,255,255,0.2);">Usable Hosts</th>'
                        '</tr>'
                        '<tr><td style="padding:5px;border:1px solid rgba(255,255,255,0.2);">/24</td>'
                        '<td style="padding:5px;border:1px solid rgba(255,255,255,0.2);">255.255.255.0</td>'
                        '<td style="padding:5px;border:1px solid rgba(255,255,255,0.2);">254</td></tr>'
                        '<tr><td style="padding:5px;border:1px solid rgba(255,255,255,0.2);">/25</td>'
                        '<td style="padding:5px;border:1px solid rgba(255,255,255,0.2);">255.255.255.128</td>'
                        '<td style="padding:5px;border:1px solid rgba(255,255,255,0.2);">126</td></tr>'
                        '<tr><td style="padding:5px;border:1px solid rgba(255,255,255,0.2);">/26</td>'
                        '<td style="padding:5px;border:1px solid rgba(255,255,255,0.2);">255.255.255.192</td>'
                        '<td style="padding:5px;border:1px solid rgba(255,255,255,0.2);">62</td></tr>'
                        '<tr><td style="padding:5px;border:1px solid rgba(255,255,255,0.2);">/27</td>'
                        '<td style="padding:5px;border:1px solid rgba(255,255,255,0.2);">255.255.255.224</td>'
                        '<td style="padding:5px;border:1px solid rgba(255,255,255,0.2);">30</td></tr>'
                        '<tr><td style="padding:5px;border:1px solid rgba(255,255,255,0.2);">/28</td>'
                        '<td style="padding:5px;border:1px solid rgba(255,255,255,0.2);">255.255.255.240</td>'
                        '<td style="padding:5px;border:1px solid rgba(255,255,255,0.2);">14</td></tr>'
                        '<tr><td style="padding:5px;border:1px solid rgba(255,255,255,0.2);">/30</td>'
                        '<td style="padding:5px;border:1px solid rgba(255,255,255,0.2);">255.255.255.252</td>'
                        '<td style="padding:5px;border:1px solid rgba(255,255,255,0.2);">2 (point-to-point links)</td></tr>'
                        '</table>'
                    ),
                    'order_index': 2,
                    'section_type': 'lesson'
                }
            ],
            'questions': [
                {
                    'question_text': 'How many usable host addresses are available in the subnet 192.168.10.0/27?',
                    'option_a': '32',
                    'option_b': '30',
                    'option_c': '28',
                    'option_d': '16',
                    'correct_answer': 'B',
                    'explanation': 'A /27 leaves 5 host bits. 2^5 = 32 addresses total. Subtract 2 (network and broadcast) = 30 usable hosts.'
                },
                {
                    'question_text': 'Which of the following is a valid private IP address per RFC 1918?',
                    'option_a': '172.32.0.1',
                    'option_b': '192.169.1.1',
                    'option_c': '10.255.255.254',
                    'option_d': '128.0.0.1',
                    'correct_answer': 'C',
                    'explanation': '10.255.255.254 falls in the 10.0.0.0/8 private range. 172.32.0.1 is outside the 172.16.0.0/12 range, and 192.169.1.1 is outside the 192.168.0.0/16 range.'
                },
                {
                    'question_text': 'An engineer needs to create 6 subnets from the 192.168.5.0/24 network. What is the minimum prefix length needed?',
                    'option_a': '/25',
                    'option_b': '/26',
                    'option_c': '/27',
                    'option_d': '/28',
                    'correct_answer': 'C',
                    'explanation': 'To create at least 6 subnets: 2^s ≥ 6. 2^2=4 (not enough), 2^3=8 (sufficient). Borrowing 3 bits from /24 gives /27, which creates 8 subnets.'
                },
                {
                    'question_text': 'What is the broadcast address for the subnet 10.0.0.0/24?',
                    'option_a': '10.0.0.0',
                    'option_b': '10.0.0.1',
                    'option_c': '10.0.0.254',
                    'option_d': '10.0.0.255',
                    'correct_answer': 'D',
                    'explanation': 'The /24 subnet 10.0.0.0 spans 10.0.0.0 to 10.0.0.255. The last address (10.0.0.255) is always the broadcast address.'
                },
                {
                    'question_text': 'Which address range is used for IPv4 loopback testing?',
                    'option_a': '169.254.0.0/16',
                    'option_b': '127.0.0.0/8',
                    'option_c': '0.0.0.0/8',
                    'option_d': '224.0.0.0/4',
                    'correct_answer': 'B',
                    'explanation': 'The 127.0.0.0/8 range is reserved for loopback. 127.0.0.1 (localhost) is used to test the TCP/IP stack on a local device. 169.254.0.0/16 is APIPA.'
                }
            ]
        },
        {
            'title': 'Switching & VLANs',
            'description': 'Configure Ethernet switches, VLANs, STP, and EtherChannel.',
            'order_index': 3,
            'points': 100,
            'icon': '🔀',
            'sections': [
                {
                    'title': 'Switch Operation & MAC Address Learning',
                    'content': (
                        '<h4>How a Switch Forwards Frames</h4>'
                        '<ol>'
                        '<li><strong>Learn</strong> - when a frame arrives, the switch records the source MAC '
                        'address and ingress port in its MAC address table (CAM table).</li>'
                        '<li><strong>Flood</strong> - if the destination MAC is unknown, the switch floods the '
                        'frame out all ports except the ingress port.</li>'
                        '<li><strong>Forward</strong> - if the destination MAC is known, the switch forwards '
                        'the frame only to the correct port.</li>'
                        '<li><strong>Filter</strong> - if source and destination are on the same port, the '
                        'frame is dropped.</li>'
                        '</ol>'
                        '<h4>Duplex & Speed</h4>'
                        '<ul>'
                        '<li><strong>Half-duplex</strong> - can only send or receive at one time (hubs, legacy).</li>'
                        '<li><strong>Full-duplex</strong> - can send and receive simultaneously; standard for '
                        'modern switches; eliminates collisions.</li>'
                        '</ul>'
                        '<h4>Cisco Switch Port Security</h4>'
                        '<p>Limits the number of MAC addresses allowed on a port. Violation modes: '
                        '<strong>Shutdown</strong> (default; disables the port), '
                        '<strong>Restrict</strong> (drops frames, increments counter), '
                        '<strong>Protect</strong> (drops frames silently).</p>'
                    ),
                    'order_index': 1,
                    'section_type': 'lesson'
                },
                {
                    'title': 'VLANs & Trunking',
                    'content': (
                        '<h4>VLANs (Virtual Local Area Networks)</h4>'
                        '<p>VLANs logically segment a network into separate broadcast domains without requiring '
                        'physical separation. Benefits: security, performance, simplified management.</p>'
                        '<ul>'
                        '<li><strong>Access port</strong> - carries traffic for a single VLAN; connects end devices.</li>'
                        '<li><strong>Trunk port</strong> - carries traffic for multiple VLANs using 802.1Q tagging; '
                        'connects switches or routers.</li>'
                        '<li><strong>Native VLAN</strong> - the VLAN whose frames traverse a trunk untagged (default VLAN 1; '
                        'best practice: change to an unused VLAN).</li>'
                        '</ul>'
                        '<h4>802.1Q Trunking</h4>'
                        '<p>IEEE 802.1Q inserts a 4-byte tag into the Ethernet frame between the source MAC and '
                        'EtherType fields. The tag includes a 12-bit VLAN ID (VID), allowing 4,094 VLANs.</p>'
                        '<h4>Inter-VLAN Routing</h4>'
                        '<ul>'
                        '<li><strong>Router on a Stick</strong> - single router interface with sub-interfaces, '
                        'one per VLAN; trunk link between switch and router.</li>'
                        '<li><strong>Layer 3 Switch (SVI)</strong> - switch with IP routing capability; '
                        'Switch Virtual Interfaces (SVIs) route between VLANs at wire speed.</li>'
                        '</ul>'
                    ),
                    'order_index': 2,
                    'section_type': 'lesson'
                }
            ],
            'questions': [
                {
                    'question_text': 'Which switch port type carries traffic for multiple VLANs using 802.1Q tags?',
                    'option_a': 'Access port',
                    'option_b': 'Trunk port',
                    'option_c': 'Mirror port',
                    'option_d': 'Native port',
                    'correct_answer': 'B',
                    'explanation': 'A trunk port carries traffic from multiple VLANs by inserting 802.1Q VLAN tags into Ethernet frames to identify which VLAN the frame belongs to.'
                },
                {
                    'question_text': 'A switch receives a frame with an unknown destination MAC address. What does it do?',
                    'option_a': 'Drops the frame',
                    'option_b': 'Sends the frame back to the source',
                    'option_c': 'Floods the frame out all ports except the ingress port',
                    'option_d': 'Forwards the frame to the default gateway',
                    'correct_answer': 'C',
                    'explanation': 'When a destination MAC is not in the CAM table, the switch floods the frame out all ports except where it arrived (unknown unicast flooding).'
                },
                {
                    'question_text': 'Which Spanning Tree Protocol port state actively forwards frames?',
                    'option_a': 'Blocking',
                    'option_b': 'Listening',
                    'option_c': 'Learning',
                    'option_d': 'Forwarding',
                    'correct_answer': 'D',
                    'explanation': 'Only a port in the Forwarding state actively sends and receives user data frames. Blocking prevents loops; Listening and Learning are transitional states.'
                },
                {
                    'question_text': 'What is the default port security violation mode on a Cisco switch?',
                    'option_a': 'Protect',
                    'option_b': 'Restrict',
                    'option_c': 'Shutdown',
                    'option_d': 'Err-disabled',
                    'correct_answer': 'C',
                    'explanation': 'The default port security violation mode is Shutdown, which places the port in err-disabled state when a violation occurs.'
                },
                {
                    'question_text': 'Which method is MOST efficient for routing between VLANs at wire speed within a campus network?',
                    'option_a': 'Router on a Stick (sub-interfaces)',
                    'option_b': 'Layer 3 Switch with SVIs',
                    'option_c': 'Dedicated physical router per VLAN',
                    'option_d': 'Proxy ARP',
                    'correct_answer': 'B',
                    'explanation': 'Layer 3 switches with Switch Virtual Interfaces (SVIs) perform inter-VLAN routing in hardware at wire speed, which is far more efficient than software-based router-on-a-stick.'
                }
            ]
        },
        {
            'title': 'Routing Protocols & WAN',
            'description': 'Configure static routes, OSPF, EIGRP concepts, and WAN technologies.',
            'order_index': 4,
            'points': 75,
            'icon': '🗺️',
            'sections': [
                {
                    'title': 'Static Routing & Administrative Distance',
                    'content': (
                        '<h4>Static Routes</h4>'
                        '<p>Manually configured routes. Best for: small networks, stub networks, '
                        'providing a default gateway (default route: 0.0.0.0/0).</p>'
                        '<p>Cisco IOS: <code style="background:rgba(0,0,0,0.3);padding:2px 6px;border-radius:3px;">'
                        'ip route [destination] [mask] [next-hop | exit-interface]</code></p>'
                        '<h4>Administrative Distance (AD)</h4>'
                        '<p>When multiple routing sources provide a route to the same destination, the router '
                        'selects the route with the <strong>lowest AD</strong> (most trustworthy source).</p>'
                        '<table style="width:100%;border-collapse:collapse;font-size:0.9rem;">'
                        '<tr style="background:rgba(4,159,217,0.3);">'
                        '<th style="padding:6px;border:1px solid rgba(255,255,255,0.2);">Source</th>'
                        '<th style="padding:6px;border:1px solid rgba(255,255,255,0.2);">AD</th>'
                        '</tr>'
                        '<tr><td style="padding:5px;border:1px solid rgba(255,255,255,0.2);">Connected interface</td>'
                        '<td style="padding:5px;border:1px solid rgba(255,255,255,0.2);">0</td></tr>'
                        '<tr><td style="padding:5px;border:1px solid rgba(255,255,255,0.2);">Static route</td>'
                        '<td style="padding:5px;border:1px solid rgba(255,255,255,0.2);">1</td></tr>'
                        '<tr><td style="padding:5px;border:1px solid rgba(255,255,255,0.2);">OSPF</td>'
                        '<td style="padding:5px;border:1px solid rgba(255,255,255,0.2);">110</td></tr>'
                        '<tr><td style="padding:5px;border:1px solid rgba(255,255,255,0.2);">IS-IS</td>'
                        '<td style="padding:5px;border:1px solid rgba(255,255,255,0.2);">115</td></tr>'
                        '<tr><td style="padding:5px;border:1px solid rgba(255,255,255,0.2);">RIP</td>'
                        '<td style="padding:5px;border:1px solid rgba(255,255,255,0.2);">120</td></tr>'
                        '<tr><td style="padding:5px;border:1px solid rgba(255,255,255,0.2);">EIGRP (external)</td>'
                        '<td style="padding:5px;border:1px solid rgba(255,255,255,0.2);">170</td></tr>'
                        '</table>'
                    ),
                    'order_index': 1,
                    'section_type': 'lesson'
                },
                {
                    'title': 'OSPF & Dynamic Routing',
                    'content': (
                        '<h4>OSPF (Open Shortest Path First)</h4>'
                        '<p>Link-state routing protocol using Dijkstra\'s Shortest Path First (SPF) algorithm. '
                        'Classless (supports VLSM and CIDR), fast convergence, no hop count limit.</p>'
                        '<ul>'
                        '<li><strong>Hello packets</strong> - discover and maintain neighbour relationships.</li>'
                        '<li><strong>LSA (Link State Advertisement)</strong> - carries topology information '
                        'flooded to all routers in the same OSPF area.</li>'
                        '<li><strong>LSDB (Link State Database)</strong> - each router maintains an identical '
                        'database of all LSAs in the area.</li>'
                        '<li><strong>DR/BDR</strong> - on multi-access networks, a Designated Router (DR) and '
                        'Backup DR (BDR) are elected to reduce OSPF traffic.</li>'
                        '<li><strong>Router ID</strong> - unique 32-bit number identifying each OSPF router; '
                        'typically the highest loopback or interface IP.</li>'
                        '</ul>'
                        '<h4>OSPF Neighbour States</h4>'
                        '<p>Down → Init → 2-Way → Exstart → Exchange → Loading → <strong>Full</strong></p>'
                        '<p>Neighbours must reach the Full state to exchange complete routing information.</p>'
                    ),
                    'order_index': 2,
                    'section_type': 'lesson'
                }
            ],
            'questions': [
                {
                    'question_text': 'Which routing source has the LOWEST administrative distance on a Cisco router?',
                    'option_a': 'OSPF',
                    'option_b': 'Static route',
                    'option_c': 'Connected interface',
                    'option_d': 'RIP',
                    'correct_answer': 'C',
                    'explanation': 'Connected interfaces have an AD of 0 - the most trusted route source. Static routes are AD 1, OSPF is 110, RIP is 120.'
                },
                {
                    'question_text': 'Which OSPF packet type is used to discover and maintain neighbour relationships?',
                    'option_a': 'DBD (Database Description)',
                    'option_b': 'LSR (Link State Request)',
                    'option_c': 'Hello',
                    'option_d': 'LSU (Link State Update)',
                    'correct_answer': 'C',
                    'explanation': 'OSPF Hello packets are used to discover neighbours and form adjacencies. They are sent periodically to maintain neighbour relationships.'
                },
                {
                    'question_text': 'Which route should a Cisco router install in the routing table when both OSPF and RIP learn the same destination?',
                    'option_a': 'RIP (AD 120)',
                    'option_b': 'OSPF (AD 110)',
                    'option_c': 'Both routes - load balance',
                    'option_d': 'The most recently learned route',
                    'correct_answer': 'B',
                    'explanation': 'The router installs the route with the lowest Administrative Distance. OSPF (110) beats RIP (120) - lower AD = more trusted = preferred.'
                },
                {
                    'question_text': 'What is the default route (also called the gateway of last resort) in CIDR notation?',
                    'option_a': '255.255.255.255/32',
                    'option_b': '127.0.0.1/8',
                    'option_c': '0.0.0.0/0',
                    'option_d': '192.168.0.0/16',
                    'correct_answer': 'C',
                    'explanation': '0.0.0.0/0 matches any destination and is used as a gateway of last resort when no more specific route exists.'
                },
                {
                    'question_text': 'OSPF routers must agree on which value for a neighbour relationship to form?',
                    'option_a': 'Router ID',
                    'option_b': 'Hello and Dead intervals',
                    'option_c': 'OSPF Process ID',
                    'option_d': 'Loopback interface IP',
                    'correct_answer': 'B',
                    'explanation': 'OSPF neighbours must match Hello interval, Dead interval, Area ID, subnet mask, and authentication settings. The Process ID is locally significant only.'
                }
            ]
        },
        {
            'title': 'Network Security & Automation',
            'description': 'Configure ACLs, NAT, network security features, and intro to automation.',
            'order_index': 5,
            'points': 75,
            'icon': '🛡️',
            'sections': [
                {
                    'title': 'Access Control Lists (ACLs)',
                    'content': (
                        '<h4>What Are ACLs?</h4>'
                        '<p>ACLs are ordered lists of permit/deny statements applied to router interfaces to '
                        'filter traffic. Rules are processed top-down; first match wins. An implicit '
                        '<strong>deny all</strong> exists at the end of every ACL.</p>'
                        '<h4>Standard vs Extended ACLs</h4>'
                        '<ul>'
                        '<li><strong>Standard ACLs</strong> (numbered 1-99, 1300-1999) - filter by source IP only. '
                        'Place as close to the destination as possible.</li>'
                        '<li><strong>Extended ACLs</strong> (numbered 100-199, 2000-2699) - filter by source IP, '
                        'destination IP, protocol, and port. Place as close to the source as possible.</li>'
                        '</ul>'
                        '<h4>ACL Placement</h4>'
                        '<ul>'
                        '<li><strong>Inbound</strong> - applied before the routing decision; more efficient.</li>'
                        '<li><strong>Outbound</strong> - applied after the routing decision.</li>'
                        '</ul>'
                        '<h4>Wildcard Masks</h4>'
                        '<p>ACLs use wildcard masks (inverse of subnet mask). 0 bits = must match, 1 bits = ignore. '
                        'Wildcard for /24 = 0.0.0.255. Use "host" keyword for single IPs; "any" for all IPs.</p>'
                    ),
                    'order_index': 1,
                    'section_type': 'lesson'
                },
                {
                    'title': 'NAT & Network Automation',
                    'content': (
                        '<h4>NAT (Network Address Translation)</h4>'
                        '<ul>'
                        '<li><strong>Static NAT</strong> - one-to-one mapping of private to public IP; used for servers.</li>'
                        '<li><strong>Dynamic NAT</strong> - maps private IPs to a pool of public IPs; no port translation.</li>'
                        '<li><strong>PAT / NAT Overload</strong> - many-to-one; maps multiple private IPs to a single '
                        'public IP using unique port numbers. Most common - used in home routers.</li>'
                        '</ul>'
                        '<h4>Network Automation & Programmability</h4>'
                        '<p>Modern networks use automation to improve consistency and reduce human error. Key concepts:</p>'
                        '<ul>'
                        '<li><strong>SDN (Software-Defined Networking)</strong> - separates the control plane from the '
                        'data plane. A centralised controller manages the network.</li>'
                        '<li><strong>REST APIs</strong> - HTTP-based APIs used by network controllers (e.g., Cisco DNA '
                        'Centre) to communicate with devices. Use JSON or XML data formats.</li>'
                        '<li><strong>Ansible</strong> - agentless automation tool; uses YAML playbooks; ideal for '
                        'network configuration management.</li>'
                        '<li><strong>Python</strong> - widely used for network automation scripts; libraries: '
                        'Netmiko, NAPALM, pyATS.</li>'
                        '</ul>'
                    ),
                    'order_index': 2,
                    'section_type': 'lesson'
                }
            ],
            'questions': [
                {
                    'question_text': 'Where should an Extended ACL be placed for optimal efficiency?',
                    'option_a': 'As close to the destination as possible',
                    'option_b': 'As close to the source as possible',
                    'option_c': 'On the core switch',
                    'option_d': 'On the ISP router',
                    'correct_answer': 'B',
                    'explanation': 'Extended ACLs should be placed close to the source to block unwanted traffic as early as possible, preventing it from traversing the network unnecessarily.'
                },
                {
                    'question_text': 'Which NAT type maps multiple private IP addresses to a single public IP address using unique port numbers?',
                    'option_a': 'Static NAT',
                    'option_b': 'Dynamic NAT',
                    'option_c': 'PAT (NAT Overload)',
                    'option_d': 'Twice NAT',
                    'correct_answer': 'C',
                    'explanation': 'PAT (Port Address Translation), also called NAT Overload, maps many private IPs to one public IP by tracking sessions using unique source port numbers - used in most home and office routers.'
                },
                {
                    'question_text': 'What does the wildcard mask 0.0.0.255 match in an ACL statement?',
                    'option_a': 'Only the exact IP address specified',
                    'option_b': 'All IP addresses',
                    'option_c': 'All hosts in the same /24 network',
                    'option_d': 'Only hosts in the /8 range',
                    'correct_answer': 'C',
                    'explanation': '0.0.0.255 means the first 3 octets must match exactly (0 = check) while the last octet can be anything (255 = ignore), matching all 256 addresses in a /24 network.'
                },
                {
                    'question_text': 'Which automation tool is agentless, uses YAML playbooks, and is commonly used for network configuration management?',
                    'option_a': 'Puppet',
                    'option_b': 'Chef',
                    'option_c': 'SaltStack',
                    'option_d': 'Ansible',
                    'correct_answer': 'D',
                    'explanation': 'Ansible is agentless (uses SSH/NETCONF - no software needed on managed devices), uses YAML playbooks, and is widely adopted for network automation.'
                },
                {
                    'question_text': 'In SDN architecture, which plane is centralised in the SDN controller?',
                    'option_a': 'Data plane (forwarding plane)',
                    'option_b': 'Management plane',
                    'option_c': 'Control plane',
                    'option_d': 'Physical plane',
                    'correct_answer': 'C',
                    'explanation': 'SDN separates the control plane (routing decisions, network intelligence) from the data plane (packet forwarding). The control plane is centralised in the SDN controller.'
                }
            ]
        }
    ]

    for mod_data in ccna_modules:
        mod = PathModule(
            path_id=ccna_path.id,
            title=mod_data['title'],
            description=mod_data['description'],
            order_index=mod_data['order_index'],
            points=mod_data['points'],
            icon=mod_data['icon']
        )
        db.session.add(mod)
        db.session.flush()

        for sec in mod_data.get('sections', []):
            section = ModuleSection(
                module_id=mod.id,
                title=sec['title'],
                content=sec['content'],
                order_index=sec['order_index'],
                section_type=sec['section_type']
            )
            db.session.add(section)

        for q in mod_data.get('questions', []):
            question = QuizQuestion(
                module_id=mod.id,
                question_text=q['question_text'],
                option_a=q['option_a'],
                option_b=q['option_b'],
                option_c=q['option_c'],
                option_d=q['option_d'],
                correct_answer=q['correct_answer'],
                explanation=q.get('explanation', '')
            )
            db.session.add(question)

    db.session.commit()
    print("Learning paths seeded successfully.")


def seed_aws_associate_paths():
    """Seed the three AWS Associate-level paths. Called from __init__.py after seed_learning_paths()."""
    existing_slugs = {p.slug for p in LearningPath.query.all()}

    paths_to_add = [
        {
            'slug': 'aws-solutions-architect-associate',
            'title': 'AWS Solutions Architect - Associate',
            'subtitle': 'SAA-C03 Certification Track',
            'description': 'Design resilient, high-performing, secure and cost-optimised AWS architectures. Covers EC2, VPC, S3, RDS, Route 53, ELB, Auto Scaling, IAM, and CloudFormation.',
            'difficulty': 'Intermediate',
            'estimated_hours': 40,
            'total_points': 225,
            'icon': '🏗️',
            'modules': [
                {
                    'title': 'Designing Resilient Architectures',
                    'description': 'Multi-AZ deployments, Auto Scaling, and Elastic Load Balancing.',
                    'order_index': 1, 'points': 75, 'icon': '🔄',
                    'sections': [
                        {'title': 'High Availability and Fault Tolerance',
                         'content': '<h4>Multi-AZ and Multi-Region</h4><p>Resilient architectures distribute workloads across multiple Availability Zones (AZs) to eliminate single points of failure. Each AZ is one or more physically separate data centres with independent power, cooling, and networking. Multi-AZ RDS automatically provisions a standby replica in a different AZ and fails over within 1-2 minutes. Multi-Region goes further, serving traffic from geographically distant regions.</p><h4>Elastic Load Balancing (ELB)</h4><ul><li><strong>Application Load Balancer (ALB)</strong> - Layer 7, HTTP/HTTPS, path-based and host-based routing.</li><li><strong>Network Load Balancer (NLB)</strong> - Layer 4, TCP/UDP, ultra-low latency, static IPs.</li><li><strong>Gateway Load Balancer (GWLB)</strong> - For third-party virtual appliances.</li></ul><h4>Auto Scaling</h4><p>EC2 Auto Scaling maintains the desired number of instances. Scaling policies: Target Tracking (e.g. keep CPU at 50%), Step Scaling (scale by different amounts at different thresholds), Scheduled Scaling. Use launch templates over launch configurations.</p>',
                         'order_index': 1, 'section_type': 'lesson'},
                        {'title': 'Decoupling with SQS and SNS',
                         'content': '<h4>Amazon SQS</h4><p>Simple Queue Service is a fully managed message queue that decouples application components. Standard queues offer at-least-once delivery and maximum throughput. FIFO queues guarantee exactly-once processing and ordering. Visibility timeout prevents duplicate processing. Dead-letter queues (DLQ) capture messages that fail processing repeatedly.</p><h4>Amazon SNS</h4><p>Simple Notification Service provides pub/sub messaging. A single SNS topic can fan out to multiple SQS queues, Lambda functions, HTTP endpoints, and email addresses simultaneously. Used for event notifications, mobile push, and fan-out patterns.</p>',
                         'order_index': 2, 'section_type': 'lesson'},
                    ],
                    'questions': [
                        {'question_text': 'Which ELB type operates at Layer 7 and supports path-based routing?',
                         'option_a': 'Network Load Balancer', 'option_b': 'Application Load Balancer',
                         'option_c': 'Gateway Load Balancer', 'option_d': 'Classic Load Balancer',
                         'correct_answer': 'B', 'explanation': 'ALB operates at Layer 7 (HTTP/HTTPS) and supports content-based routing including path-based (/api/*) and host-based (api.example.com) rules.'},
                        {'question_text': 'An SQS queue is receiving messages faster than they can be processed. What feature captures messages that fail processing repeatedly?',
                         'option_a': 'Visibility timeout', 'option_b': 'Long polling', 'option_c': 'Dead-letter queue', 'option_d': 'FIFO queue',
                         'correct_answer': 'C', 'explanation': 'Dead-letter queues (DLQ) capture messages that have exceeded the maximum receive count, preventing them from blocking the main queue.'},
                        {'question_text': 'Which Auto Scaling policy maintains a specific metric at a target value, such as keeping average CPU utilisation at 50%?',
                         'option_a': 'Step Scaling', 'option_b': 'Scheduled Scaling', 'option_c': 'Simple Scaling', 'option_d': 'Target Tracking Scaling',
                         'correct_answer': 'D', 'explanation': 'Target Tracking Scaling automatically adjusts capacity to keep a chosen metric at a target value — no need to define scale-in/scale-out steps.'},
                        {'question_text': 'Multi-AZ RDS provides which primary benefit?',
                         'option_a': 'Read performance improvement', 'option_b': 'Automatic failover for high availability', 'option_c': 'Lower storage costs', 'option_d': 'Cross-region replication',
                         'correct_answer': 'B', 'explanation': 'Multi-AZ RDS provisions a synchronous standby replica in a different AZ. On failure, RDS automatically fails over to the standby with minimal downtime. It does NOT improve read performance -- use Read Replicas for that.'},
                        {'question_text': 'Which SQS queue type guarantees exactly-once message delivery and strict ordering?',
                         'option_a': 'Standard Queue', 'option_b': 'Dead-Letter Queue', 'option_c': 'FIFO Queue', 'option_d': 'Priority Queue',
                         'correct_answer': 'C', 'explanation': 'FIFO (First-In-First-Out) queues guarantee exactly-once processing and strict ordering. Standard queues offer best-effort ordering and at-least-once delivery with higher throughput.'},
                    ]
                },
                {
                    'title': 'Networking and Content Delivery',
                    'description': 'VPC design, Route 53, CloudFront, and hybrid connectivity.',
                    'order_index': 2, 'points': 75, 'icon': '🌐',
                    'sections': [
                        {'title': 'VPC Design and Subnets',
                         'content': '<h4>VPC Fundamentals</h4><p>A Virtual Private Cloud is a logically isolated section of AWS. Each VPC has a CIDR block (e.g. 10.0.0.0/16). Subnets are subdivisions tied to a single AZ. Public subnets have a route to an Internet Gateway (IGW). Private subnets route outbound internet traffic through a NAT Gateway.</p><h4>Security Controls</h4><ul><li><strong>Security Groups</strong> - Stateful, instance-level firewall. Return traffic is automatically allowed.</li><li><strong>Network ACLs</strong> - Stateless, subnet-level. Must explicitly allow inbound AND outbound.</li></ul><h4>VPC Peering and PrivateLink</h4><p>VPC Peering connects two VPCs with non-overlapping CIDRs (not transitive). AWS PrivateLink provides private connectivity to AWS services or other VPCs without traversing the internet.</p>',
                         'order_index': 1, 'section_type': 'lesson'},
                        {'title': 'Route 53 and CloudFront',
                         'content': '<h4>Amazon Route 53</h4><p>Route 53 is AWS\'s highly available DNS service. Routing policies: Simple (single resource), Weighted (A/B testing), Latency (serve from lowest-latency region), Failover (active-passive HA), Geolocation (route by user location), Geoproximity, Multivalue Answer. Health checks monitor endpoint availability and trigger failover automatically.</p><h4>Amazon CloudFront</h4><p>CloudFront is a Content Delivery Network (CDN) that caches content at 400+ edge locations globally. Reduces latency and origin load. Integrates with S3 (Origin Access Control restricts S3 to CloudFront only), ALB, and custom origins. Use signed URLs/cookies for private content. Lambda@Edge runs code at edge locations.</p>',
                         'order_index': 2, 'section_type': 'lesson'},
                    ],
                    'questions': [
                        {'question_text': 'Which Route 53 routing policy distributes traffic to multiple resources in proportions you specify?',
                         'option_a': 'Latency', 'option_b': 'Failover', 'option_c': 'Weighted', 'option_d': 'Geolocation',
                         'correct_answer': 'C', 'explanation': 'Weighted routing lets you assign weights (0-255) to record sets. Useful for A/B testing and gradual traffic migration between regions or versions.'},
                        {'question_text': 'A security group and a Network ACL both protect VPC resources. What is the key difference?',
                         'option_a': 'Security groups are stateless; NACLs are stateful', 'option_b': 'Security groups are stateful; NACLs are stateless',
                         'option_c': 'Both are stateless', 'option_d': 'Both are stateful',
                         'correct_answer': 'B', 'explanation': 'Security groups are stateful -- if inbound traffic is allowed, the return traffic is automatically allowed. NACLs are stateless -- you must explicitly allow both inbound and outbound traffic.'},
                        {'question_text': 'Which CloudFront feature restricts S3 bucket access so only CloudFront can serve the content?',
                         'option_a': 'Lambda@Edge', 'option_b': 'Signed URLs', 'option_c': 'Origin Access Control (OAC)', 'option_d': 'WAF integration',
                         'correct_answer': 'C', 'explanation': 'Origin Access Control (OAC) -- the successor to Origin Access Identity -- restricts your S3 bucket so it only accepts requests from your CloudFront distribution, preventing direct S3 access.'},
                        {'question_text': 'Private subnets in a VPC need internet access for updates. What AWS resource provides this without exposing instances to inbound internet traffic?',
                         'option_a': 'Internet Gateway', 'option_b': 'NAT Gateway', 'option_c': 'VPC Peering', 'option_d': 'Transit Gateway',
                         'correct_answer': 'B', 'explanation': 'A NAT Gateway allows instances in private subnets to initiate outbound internet connections (for updates, patches, API calls) while blocking unsolicited inbound connections from the internet.'},
                        {'question_text': 'VPC Peering has which important limitation?',
                         'option_a': 'It requires overlapping CIDR blocks', 'option_b': 'It only works within the same region', 'option_c': 'It is not transitive', 'option_d': 'It does not support IPv6',
                         'correct_answer': 'C', 'explanation': 'VPC Peering is not transitive. If VPC-A peers with VPC-B and VPC-B peers with VPC-C, VPC-A cannot communicate with VPC-C through VPC-B. You need a direct peering or AWS Transit Gateway for transitive routing.'},
                    ]
                },
                {
                    'title': 'Storage, Databases, and Cost Optimisation',
                    'description': 'S3 storage classes, RDS, DynamoDB, and cost strategies.',
                    'order_index': 3, 'points': 75, 'icon': '💾',
                    'sections': [
                        {'title': 'S3 Storage Classes and Lifecycle',
                         'content': '<h4>S3 Storage Classes</h4><table><tr><th>Class</th><th>Use Case</th><th>Retrieval</th></tr><tr><td>S3 Standard</td><td>Frequently accessed data</td><td>Milliseconds</td></tr><tr><td>S3 Standard-IA</td><td>Infrequently accessed, rapid retrieval</td><td>Milliseconds</td></tr><tr><td>S3 One Zone-IA</td><td>Non-critical, infrequently accessed</td><td>Milliseconds</td></tr><tr><td>S3 Glacier Instant</td><td>Archives, millisecond access</td><td>Milliseconds</td></tr><tr><td>S3 Glacier Flexible</td><td>Archives, hours retrieval</td><td>Minutes to hours</td></tr><tr><td>S3 Glacier Deep Archive</td><td>Long-term archives</td><td>Up to 12 hours</td></tr><tr><td>S3 Intelligent-Tiering</td><td>Unknown/changing access patterns</td><td>Milliseconds</td></tr></table><h4>Lifecycle Policies</h4><p>Automatically transition objects between storage classes or expire them after a defined number of days. Example: Standard -> Standard-IA after 30 days -> Glacier after 90 days -> Delete after 365 days.</p>',
                         'order_index': 1, 'section_type': 'lesson'},
                        {'title': 'RDS, DynamoDB, and Cost Strategies',
                         'content': '<h4>Amazon RDS</h4><p>Managed relational database supporting MySQL, PostgreSQL, MariaDB, Oracle, SQL Server, and Aurora. Read Replicas improve read throughput (up to 5 per primary, up to 15 for Aurora). Multi-AZ provides HA. Aurora is AWS-optimised, 5x faster than MySQL, storage auto-scales to 128 TB.</p><h4>Amazon DynamoDB</h4><p>Serverless NoSQL key-value and document database. Single-digit millisecond performance at any scale. On-demand capacity mode for unpredictable traffic. Provisioned mode for predictable traffic with Auto Scaling. DynamoDB Streams captures changes for event-driven architectures. DAX (DynamoDB Accelerator) provides in-memory caching, microsecond reads.</p><h4>Cost Optimisation Strategies</h4><ul><li><strong>Reserved Instances</strong> - Up to 72% off On-Demand for 1 or 3-year commitment.</li><li><strong>Savings Plans</strong> - Flexible commitment ($/hour) across instance families.</li><li><strong>Spot Instances</strong> - Up to 90% off for fault-tolerant, interruptible workloads.</li><li><strong>Right-sizing</strong> - Match instance type to actual resource usage using Cost Explorer.</li></ul>',
                         'order_index': 2, 'section_type': 'lesson'},
                    ],
                    'questions': [
                        {'question_text': 'Which S3 storage class automatically moves objects between tiers based on changing access patterns with no retrieval fees?',
                         'option_a': 'S3 Standard-IA', 'option_b': 'S3 Intelligent-Tiering', 'option_c': 'S3 Glacier Instant', 'option_d': 'S3 One Zone-IA',
                         'correct_answer': 'B', 'explanation': 'S3 Intelligent-Tiering automatically moves objects to the most cost-effective tier based on access patterns, with no retrieval fees and no minimum storage duration for the Frequent Access tier.'},
                        {'question_text': 'Aurora provides how many copies of your data across Availability Zones?',
                         'option_a': '2', 'option_b': '3', 'option_c': '6', 'option_d': '12',
                         'correct_answer': 'C', 'explanation': 'Aurora maintains 6 copies of your data across 3 AZs (2 copies per AZ) and can tolerate the loss of up to 2 copies for writes and 3 copies for reads.'},
                        {'question_text': 'Which EC2 pricing model offers up to 90% discount and is best suited for fault-tolerant batch processing workloads?',
                         'option_a': 'Reserved Instances', 'option_b': 'Dedicated Hosts', 'option_c': 'Spot Instances', 'option_d': 'Savings Plans',
                         'correct_answer': 'C', 'explanation': 'Spot Instances use spare EC2 capacity at up to 90% discount. AWS can reclaim them with a 2-minute warning, making them ideal for fault-tolerant workloads like batch jobs, data analysis, and CI/CD.'},
                        {'question_text': 'DynamoDB DAX provides which performance improvement?',
                         'option_a': 'Millisecond write latency', 'option_b': 'Multi-region replication', 'option_c': 'Microsecond read latency', 'option_d': 'Automated backups',
                         'correct_answer': 'C', 'explanation': 'DynamoDB Accelerator (DAX) is an in-memory cache that delivers microsecond read performance for DynamoDB. It is fully compatible with existing DynamoDB API calls -- no application code changes required.'},
                        {'question_text': 'An S3 Lifecycle policy is configured to transition objects to Glacier after 90 days. What does this mean for objects accessed on day 91?',
                         'option_a': 'They are deleted', 'option_b': 'They are retrieved in milliseconds at no extra charge', 'option_c': 'They may take minutes to hours to retrieve and incur retrieval fees', 'option_d': 'They are automatically moved back to Standard',
                         'correct_answer': 'C', 'explanation': 'S3 Glacier Flexible Retrieval has retrieval times of minutes (Expedited) to hours (Standard, Bulk) and charges retrieval fees. For millisecond access to archived objects, use S3 Glacier Instant Retrieval instead.'},
                    ]
                }
            ]
        },
        {
            'slug': 'aws-developer-associate',
            'title': 'AWS Developer - Associate',
            'subtitle': 'DVA-C02 Certification Track',
            'description': 'Build and deploy cloud-native applications on AWS. Covers Lambda, API Gateway, DynamoDB, CodePipeline, CloudFormation, ECS, and application security best practices.',
            'difficulty': 'Intermediate',
            'estimated_hours': 35,
            'total_points': 225,
            'icon': '👨‍💻',
            'modules': [
                {
                    'title': 'Serverless Development with Lambda',
                    'description': 'Lambda functions, event sources, and API Gateway integration.',
                    'order_index': 1, 'points': 75, 'icon': 'λ',
                    'sections': [
                        {'title': 'AWS Lambda Deep Dive',
                         'content': '<h4>Lambda Fundamentals</h4><p>AWS Lambda runs code without provisioning or managing servers. You pay only for compute time consumed (per 100ms). Supports Python, Node.js, Java, C#, Go, Ruby, and custom runtimes. Max execution timeout is 15 minutes. Memory: 128 MB to 10 GB. Each function invocation gets 512 MB of /tmp ephemeral storage (up to 10 GB).</p><h4>Invocation Models</h4><ul><li><strong>Synchronous</strong> - API Gateway, ALB, SDK calls. Caller waits for response.</li><li><strong>Asynchronous</strong> - S3 events, SNS, EventBridge. Lambda retries up to 2 times on error.</li><li><strong>Poll-based (Streaming)</strong> - SQS, Kinesis, DynamoDB Streams. Lambda polls the source.</li></ul><h4>Lambda Concurrency</h4><p>Reserved concurrency guarantees a maximum concurrent execution limit for a function. Provisioned concurrency pre-warms execution environments to eliminate cold starts. Account-level concurrency limit: 1,000 concurrent executions (soft limit, can be raised).</p><h4>Lambda@Edge and CloudFront Functions</h4><p>Lambda@Edge runs at CloudFront edge locations for viewer/origin request and response manipulation. CloudFront Functions are lighter-weight and cheaper, for simple URL rewrites and header manipulations.</p>',
                         'order_index': 1, 'section_type': 'lesson'},
                        {'title': 'API Gateway',
                         'content': '<h4>Amazon API Gateway</h4><p>Fully managed service for creating, publishing, and securing REST, HTTP, and WebSocket APIs. Integrates natively with Lambda, enabling serverless backends. Key features: request/response transformation, request validation, API keys, usage plans, throttling (per-client rate limits), caching (TTL 0-3600s), and custom domain names.</p><h4>REST API vs HTTP API</h4><ul><li><strong>REST API</strong> - Full features: request validation, response transformation, caching, API keys, WAF. Higher cost.</li><li><strong>HTTP API</strong> - Simpler, up to 71% cheaper. Supports JWT authorisers, OIDC, OAuth 2.0. Recommended for Lambda proxies.</li></ul><h4>Deployment Stages and Canary Releases</h4><p>APIs are deployed to stages (dev, staging, prod). Stage variables function like environment variables for stages. Canary deployments split traffic between the current stage and a new version at a configurable percentage.</p>',
                         'order_index': 2, 'section_type': 'lesson'},
                    ],
                    'questions': [
                        {'question_text': 'What is the maximum execution timeout for an AWS Lambda function?',
                         'option_a': '5 minutes', 'option_b': '10 minutes', 'option_c': '15 minutes', 'option_d': '30 minutes',
                         'correct_answer': 'C', 'explanation': 'Lambda functions have a maximum execution timeout of 15 minutes (900 seconds). For longer-running workloads, consider AWS Fargate, EC2, or AWS Batch.'},
                        {'question_text': 'Which Lambda concurrency feature eliminates cold starts by pre-warming execution environments?',
                         'option_a': 'Reserved concurrency', 'option_b': 'Provisioned concurrency', 'option_c': 'Enhanced concurrency', 'option_d': 'Account concurrency',
                         'correct_answer': 'B', 'explanation': 'Provisioned concurrency initialises a requested number of execution environments so they are prepared to respond immediately. Reserved concurrency sets a ceiling on concurrent executions but does not eliminate cold starts.'},
                        {'question_text': 'Which API Gateway type is recommended for new Lambda integrations due to lower cost and simpler configuration?',
                         'option_a': 'REST API', 'option_b': 'WebSocket API', 'option_c': 'HTTP API', 'option_d': 'Private API',
                         'correct_answer': 'C', 'explanation': 'HTTP APIs are up to 71% cheaper than REST APIs and are the recommended choice for Lambda proxy integrations. Use REST APIs when you need request validation, caching, API keys, or WAF integration.'},
                        {'question_text': 'An S3 bucket event triggers a Lambda function that fails. How many times will Lambda automatically retry?',
                         'option_a': '0', 'option_b': '1', 'option_c': '2', 'option_d': '3',
                         'correct_answer': 'C', 'explanation': 'For asynchronous invocations (including S3 events), Lambda automatically retries failed invocations up to 2 additional times (3 total attempts). Configure a dead-letter queue (SQS/SNS) to capture events that exhaust retries.'},
                        {'question_text': 'Which feature allows API Gateway to serve different traffic percentages to two versions of the same stage?',
                         'option_a': 'Stage variables', 'option_b': 'Canary release', 'option_c': 'Usage plans', 'option_d': 'Method throttling',
                         'correct_answer': 'B', 'explanation': 'Canary releases in API Gateway allow you to route a configurable percentage of traffic to a new stage version, enabling gradual rollout and easy rollback of API changes.'},
                    ]
                },
                {
                    'title': 'CI/CD with AWS Developer Tools',
                    'description': 'CodeCommit, CodeBuild, CodeDeploy, and CodePipeline.',
                    'order_index': 2, 'points': 75, 'icon': '🔄',
                    'sections': [
                        {'title': 'AWS Developer Tools Pipeline',
                         'content': '<h4>CodeCommit</h4><p>Fully managed Git repository service. Private repositories, IAM-based access control, encryption at rest and in transit. Triggers can invoke Lambda or send SNS notifications on repository events.</p><h4>CodeBuild</h4><p>Fully managed build service that compiles source code, runs tests, and produces build artefacts. Build instructions defined in buildspec.yml in the root of the source directory. Phases: install, pre_build, build, post_build. Supports Docker, outputs to S3. Pay per build minute.</p><h4>CodeDeploy</h4><p>Automates application deployments to EC2, on-premises servers, Lambda, and ECS. Deployment configurations: In-Place (EC2 only), Blue/Green. For Lambda: Linear (shift traffic in equal increments), Canary (shift a percentage then remainder), All-at-once. Deployment hooks (BeforeInstall, AfterInstall, ApplicationStart, ValidateService) run lifecycle scripts.</p><h4>CodePipeline</h4><p>Continuous delivery service that orchestrates source, build, test, and deploy stages. Integrates with CodeCommit, GitHub, CodeBuild, CodeDeploy, CloudFormation, ECS, and third-party tools. Each stage has one or more actions. Parallel actions within a stage run simultaneously.</p>',
                         'order_index': 1, 'section_type': 'lesson'},
                        {'title': 'CloudFormation and CDK',
                         'content': '<h4>AWS CloudFormation</h4><p>Infrastructure as Code service that provisions AWS resources from JSON or YAML templates. Key sections: AWSTemplateFormatVersion, Description, Parameters (input values), Mappings (static lookup tables), Conditions, Resources (required - defines AWS resources), Outputs. StackSets deploy stacks across multiple accounts and regions. Change Sets preview changes before applying. Drift detection identifies resources that have changed outside CloudFormation.</p><h4>AWS CDK (Cloud Development Kit)</h4><p>Define cloud infrastructure using familiar programming languages (Python, TypeScript, Java, C#). CDK apps are synthesised into CloudFormation templates. Constructs are reusable cloud components. Three levels: L1 (CloudFormation resource, cfn_ prefix), L2 (higher-level with defaults), L3 (patterns, complete solutions). CDK is increasingly preferred for complex infrastructure.</p>',
                         'order_index': 2, 'section_type': 'lesson'},
                    ],
                    'questions': [
                        {'question_text': 'Where does CodeBuild look for build instructions in your source repository?',
                         'option_a': 'Makefile', 'option_b': 'buildspec.yml', 'option_c': 'Dockerfile', 'option_d': 'appspec.yml',
                         'correct_answer': 'B', 'explanation': 'CodeBuild looks for buildspec.yml in the root of the source directory. It defines the phases (install, pre_build, build, post_build), environment variables, and artefacts. You can also define the buildspec inline in the CodeBuild project configuration.'},
                        {'question_text': 'A CodeDeploy Blue/Green deployment to Lambda shifts 10% of traffic immediately then the remaining 90% after 10 minutes. Which configuration is this?',
                         'option_a': 'All-at-once', 'option_b': 'Linear10PercentEvery10Minutes', 'option_c': 'Canary10Percent10Minutes', 'option_d': 'OneAtATime',
                         'correct_answer': 'C', 'explanation': 'Canary deployments shift a specified percentage of traffic initially, wait for a period, then shift the rest. Canary10Percent10Minutes shifts 10% immediately, waits 10 minutes, then shifts the remaining 90%.'},
                        {'question_text': 'Which CloudFormation section is REQUIRED in every template?',
                         'option_a': 'Parameters', 'option_b': 'Outputs', 'option_c': 'Resources', 'option_d': 'Conditions',
                         'correct_answer': 'C', 'explanation': 'The Resources section is the only required section in a CloudFormation template. It defines the AWS resources to be provisioned. All other sections (Parameters, Mappings, Conditions, Outputs) are optional.'},
                        {'question_text': 'What does a CodePipeline Change Set stage produce?',
                         'option_a': 'A compiled application build', 'option_b': 'A preview of infrastructure changes before applying them', 'option_c': 'A Git diff of source code changes', 'option_d': 'A deployment approval notification',
                         'correct_answer': 'B', 'explanation': 'CloudFormation Change Sets preview the changes that will be made to a stack when a template is applied. They allow you to review additions, modifications, and deletions before committing to the update.'},
                        {'question_text': 'Which AWS CDK construct level provides the highest level of abstraction with complete solution patterns?',
                         'option_a': 'L1 (cfn_ constructs)', 'option_b': 'L2 (curated constructs)', 'option_c': 'L3 (patterns)', 'option_d': 'L0 (raw CloudFormation)',
                         'correct_answer': 'C', 'explanation': 'L3 constructs (patterns) are the highest level, encapsulating complete solutions like an ECS service with a load balancer and auto-scaling. L1 maps directly to CloudFormation resources. L2 adds sensible defaults and helper methods.'},
                    ]
                },
                {
                    'title': 'Application Security and Monitoring',
                    'description': 'Cognito, Secrets Manager, X-Ray, and CloudWatch for developers.',
                    'order_index': 3, 'points': 75, 'icon': '🔐',
                    'sections': [
                        {'title': 'Authentication and Secrets',
                         'content': '<h4>Amazon Cognito</h4><p>User identity and access management for web and mobile apps. <strong>User Pools</strong> provide authentication - sign-up, sign-in, MFA, and JWT tokens (ID, access, refresh). <strong>Identity Pools</strong> provide AWS credential federation - exchange social provider tokens for temporary AWS credentials via STS AssumeRoleWithWebIdentity. User Pools and Identity Pools can be used together or independently.</p><h4>AWS Secrets Manager</h4><p>Securely store, manage, and rotate secrets (database credentials, API keys, OAuth tokens). Automatic rotation uses Lambda functions. Applications retrieve secrets via API/SDK, eliminating hardcoded credentials. Integrated with RDS, Redshift, and DocumentDB for automatic password rotation. Cost: $0.40/secret/month + $0.05/10,000 API calls.</p><h4>SSM Parameter Store</h4><p>Hierarchical configuration and secrets storage. Standard tier is free (up to 10,000 parameters). Advanced tier supports larger values and parameter policies (expiry, notification). SecureString parameters are encrypted with KMS. Lower cost than Secrets Manager but no automatic rotation.</p>',
                         'order_index': 1, 'section_type': 'lesson'},
                        {'title': 'X-Ray, CloudWatch, and EventBridge',
                         'content': '<h4>AWS X-Ray</h4><p>Distributed tracing service that helps debug and analyse microservices. Traces record the path of a request through your application. Segments represent work done by a service. Subsegments provide granular timing for AWS SDK calls and SQL queries. Sampling reduces trace volume in high-traffic applications. X-Ray daemon runs as a sidecar and batches trace data to the X-Ray service.</p><h4>Amazon CloudWatch for Developers</h4><p>CloudWatch Logs Insights enables interactive queries across log groups using a query language. Metric Filters extract metrics from log entries. CloudWatch Alarms trigger SNS, Auto Scaling, or EC2 actions. Embedded Metric Format (EMF) allows applications to emit custom metrics as structured log JSON, eliminating separate PutMetricData calls.</p><h4>Amazon EventBridge</h4><p>Serverless event bus connecting AWS services, SaaS applications, and custom applications. Rules match events and route to targets (Lambda, SQS, SNS, Step Functions). Scheduled rules use cron or rate expressions. Event pattern matching is JSON-based. Replaces CloudWatch Events with additional capabilities.</p>',
                         'order_index': 2, 'section_type': 'lesson'},
                    ],
                    'questions': [
                        {'question_text': 'Amazon Cognito User Pools primarily provide which capability?',
                         'option_a': 'Temporary AWS credentials for mobile users', 'option_b': 'User authentication with JWT tokens', 'option_c': 'VPC access for mobile applications', 'option_d': 'S3 presigned URL generation',
                         'correct_answer': 'B', 'explanation': 'Cognito User Pools handle user authentication -- sign-up, sign-in, MFA, forgot password -- and issue JWT tokens (ID token, access token, refresh token). Identity Pools then exchange these tokens for temporary AWS credentials.'},
                        {'question_text': 'What is the key advantage of AWS Secrets Manager over SSM Parameter Store SecureString?',
                         'option_a': 'Lower cost per secret', 'option_b': 'Larger parameter values', 'option_c': 'Automatic secret rotation', 'option_d': 'Cross-region replication',
                         'correct_answer': 'C', 'explanation': 'Secrets Manager supports automatic rotation of secrets using Lambda functions, natively integrated with RDS, Redshift, and DocumentDB. SSM Parameter Store does not support automatic rotation -- you must implement rotation manually.'},
                        {'question_text': 'In AWS X-Ray, what does a Segment represent?',
                         'option_a': 'A single HTTP request from end to end', 'option_b': 'Work done by a single service or application', 'option_c': 'A sampled subset of all traces', 'option_d': 'A timing entry for an AWS SDK call',
                         'correct_answer': 'B', 'explanation': 'An X-Ray Segment represents work done by a single service. A Trace is the complete end-to-end request. Subsegments provide detail within a segment for downstream calls, SQL queries, and SDK calls.'},
                        {'question_text': 'Which CloudWatch feature allows you to extract numeric metrics directly from application log entries?',
                         'option_a': 'CloudWatch Alarms', 'option_b': 'CloudWatch Logs Insights', 'option_c': 'Metric Filters', 'option_d': 'CloudWatch Dashboards',
                         'correct_answer': 'C', 'explanation': 'Metric Filters scan log events for specific patterns and convert matching text into CloudWatch metrics. For example, extracting error counts or response times from application logs without changing application code.'},
                        {'question_text': 'EventBridge Scheduled Rules support which scheduling expressions?',
                         'option_a': 'Only cron expressions', 'option_b': 'Only rate expressions', 'option_c': 'Both cron and rate expressions', 'option_d': 'POSIX cron only',
                         'correct_answer': 'C', 'explanation': 'EventBridge Scheduled Rules support both rate expressions (e.g. rate(5 minutes)) for simple intervals and cron expressions (e.g. cron(0 12 * * ? *)) for complex schedules. Both use UTC time.'},
                    ]
                }
            ]
        },
        {
            'slug': 'aws-sysops-administrator-associate',
            'title': 'AWS SysOps Administrator - Associate',
            'subtitle': 'SOA-C02 Certification Track',
            'description': 'Deploy, manage, and operate scalable systems on AWS. Covers monitoring, high availability, deployment automation, networking, security, and cost management.',
            'difficulty': 'Intermediate',
            'estimated_hours': 35,
            'total_points': 225,
            'icon': '🖥️',
            'modules': [
                {
                    'title': 'Monitoring, Logging, and Alerting',
                    'description': 'CloudWatch, CloudTrail, Config, and operational observability.',
                    'order_index': 1, 'points': 75, 'icon': '📊',
                    'sections': [
                        {'title': 'CloudWatch Monitoring',
                         'content': '<h4>CloudWatch Metrics</h4><p>CloudWatch collects metrics from AWS services automatically. EC2 default metrics: CPUUtilization, NetworkIn/Out, DiskReadOps/WriteOps. Detailed monitoring (1-minute intervals, additional cost) vs basic monitoring (5-minute intervals, free). Custom metrics via PutMetricData API -- standard resolution (1-minute) or high resolution (1-second). Namespaces organise metrics by service.</p><h4>CloudWatch Alarms</h4><p>Alarms monitor a metric over a specified period and trigger actions when a threshold is breached. States: OK, ALARM, INSUFFICIENT_DATA. Actions: SNS notification, EC2 action (stop/terminate/reboot/recover), Auto Scaling policy. Composite alarms combine multiple alarms with AND/OR logic. Alarm math uses metric math expressions.</p><h4>CloudWatch Logs</h4><p>Centralised log management with retention policies (1 day to never expire). Log groups contain log streams. Subscription filters stream logs to Kinesis, Lambda, or OpenSearch in real time. Logs Insights for interactive queries. Export to S3 for long-term archival.</p>',
                         'order_index': 1, 'section_type': 'lesson'},
                        {'title': 'CloudTrail, Config, and Systems Manager',
                         'content': '<h4>AWS CloudTrail</h4><p>Records API calls made to your AWS account -- who did what, from where, and when. Management events (control plane -- CreateBucket, RunInstances) are logged by default. Data events (S3 object-level, Lambda invocations) must be explicitly enabled. CloudTrail Lake stores events for querying. Enable in all regions and enable log file integrity validation for compliance.</p><h4>AWS Config</h4><p>Continuous assessment of resource configurations against desired state. Config Rules evaluate resources (AWS managed rules or custom Lambda rules). Conformance Packs group multiple rules and remediation actions. Remediation Actions automatically fix non-compliant resources (e.g. enable encryption, attach IAM policies). Config integrates with Systems Manager Automation for auto-remediation.</p><h4>AWS Systems Manager (SSM)</h4><p>Operational hub for managing EC2 and on-premises servers. Key features: Session Manager (SSH replacement, no open port 22 required), Patch Manager (automated patching with patch baselines), Parameter Store, Automation (runbooks for common tasks), Run Command (execute scripts at scale without SSH), Inventory (collect software/configuration data).</p>',
                         'order_index': 2, 'section_type': 'lesson'},
                    ],
                    'questions': [
                        {'question_text': 'EC2 basic monitoring sends metrics to CloudWatch at what interval?',
                         'option_a': '1 minute', 'option_b': '5 minutes', 'option_c': '15 minutes', 'option_d': '1 hour',
                         'correct_answer': 'B', 'explanation': 'EC2 basic monitoring (included free) sends metrics at 5-minute intervals. Detailed monitoring (additional cost) sends metrics at 1-minute intervals and is required when you need faster Auto Scaling responses.'},
                        {'question_text': 'AWS Config continuously monitors resource configurations. What does a Config Rule do?',
                         'option_a': 'Blocks non-compliant API calls in real time', 'option_b': 'Evaluates resource configurations against desired settings', 'option_c': 'Encrypts all configuration data', 'option_d': 'Creates backups of configuration changes',
                         'correct_answer': 'B', 'explanation': 'Config Rules evaluate the configuration of AWS resources against a desired state. Non-compliant resources are flagged for review or automatic remediation. They do not block changes in real time -- use SCPs or IAM for preventive controls.'},
                        {'question_text': 'Which AWS Systems Manager feature replaces SSH and does not require port 22 to be open?',
                         'option_a': 'Run Command', 'option_b': 'Patch Manager', 'option_c': 'Session Manager', 'option_d': 'Parameter Store',
                         'correct_answer': 'C', 'explanation': 'Session Manager provides secure, audited, browser-based shell access to EC2 instances without requiring SSH keys, bastion hosts, or open inbound ports. All session activity is logged to CloudWatch and/or S3.'},
                        {'question_text': 'CloudTrail logs which type of events by default without additional configuration?',
                         'option_a': 'Data events (S3 object-level operations)', 'option_b': 'Management events (API calls for resource management)', 'option_c': 'Insight events (unusual API activity)', 'option_d': 'Network events (VPC flow logs)',
                         'correct_answer': 'B', 'explanation': 'CloudTrail logs management events (control plane operations like creating, modifying, or deleting AWS resources) by default. Data events (S3 object reads/writes, Lambda invocations) must be explicitly enabled and incur additional cost.'},
                        {'question_text': 'A CloudWatch Alarm is in INSUFFICIENT_DATA state. What does this mean?',
                         'option_a': 'The alarm threshold has been breached', 'option_b': 'The metric has not exceeded the threshold', 'option_c': 'There is not enough data to determine the alarm state', 'option_d': 'The metric does not exist',
                         'correct_answer': 'C', 'explanation': 'INSUFFICIENT_DATA means the alarm has just started, the metric is not being reported, or there is not enough data collected within the evaluation period to determine whether the threshold is breached. It is not an error state.'},
                    ]
                },
                {
                    'title': 'Reliability, Backup, and Disaster Recovery',
                    'description': 'Backup strategies, DR patterns, and Route 53 health checks.',
                    'order_index': 2, 'points': 75, 'icon': '🛡️',
                    'sections': [
                        {'title': 'Disaster Recovery Strategies',
                         'content': '<h4>DR Strategies (fastest to slowest RTO/RPO)</h4><table><tr><th>Strategy</th><th>Description</th><th>Cost</th><th>RTO</th></tr><tr><td>Multi-Site Active-Active</td><td>Full production in multiple regions, simultaneous traffic</td><td>Highest</td><td>Near zero</td></tr><tr><td>Warm Standby</td><td>Scaled-down but functional copy in DR region</td><td>High</td><td>Minutes</td></tr><tr><td>Pilot Light</td><td>Core components running in DR, must scale out on failover</td><td>Medium</td><td>10s of minutes</td></tr><tr><td>Backup and Restore</td><td>Data backed up to S3/Glacier, restore from scratch on disaster</td><td>Lowest</td><td>Hours</td></tr></table><h4>Recovery Objectives</h4><ul><li><strong>RTO (Recovery Time Objective)</strong> - Maximum acceptable downtime after a disaster.</li><li><strong>RPO (Recovery Point Objective)</strong> - Maximum acceptable data loss measured in time.</li></ul>',
                         'order_index': 1, 'section_type': 'lesson'},
                        {'title': 'AWS Backup and Data Protection',
                         'content': '<h4>AWS Backup</h4><p>Centralised backup service for EC2, EBS, RDS, Aurora, DynamoDB, EFS, FSx, and S3. Backup Plans define schedule and retention. Backup Vaults store recovery points with resource-based access policies. Cross-region and cross-account backup for disaster recovery. Vault Lock (WORM - Write Once Read Many) prevents backup deletion for compliance.</p><h4>EBS Snapshots and AMIs</h4><p>EBS Snapshots are incremental backups stored in S3. First snapshot is full; subsequent snapshots store only changed blocks. Copy snapshots across regions for DR. Create AMIs from running instances for golden image management. Amazon Data Lifecycle Manager (DLM) automates snapshot and AMI creation and deletion policies.</p><h4>RDS Automated Backups and Snapshots</h4><p>RDS automated backups: retention 1-35 days, point-in-time recovery to any second within retention period. Manual DB snapshots: retained indefinitely until explicitly deleted. Restore always creates a new DB instance -- you cannot restore to an existing instance. Cross-region read replica promotion for DR.</p>',
                         'order_index': 2, 'section_type': 'lesson'},
                    ],
                    'questions': [
                        {'question_text': 'Which DR strategy maintains a fully functional but scaled-down copy of the production environment in a secondary region?',
                         'option_a': 'Backup and Restore', 'option_b': 'Pilot Light', 'option_c': 'Warm Standby', 'option_d': 'Multi-Site Active-Active',
                         'correct_answer': 'C', 'explanation': 'Warm Standby runs a scaled-down but fully functional version of the production environment in a secondary region. On failover, you scale up the standby. Faster RTO than Pilot Light but more expensive.'},
                        {'question_text': 'RPO is defined as which recovery objective?',
                         'option_a': 'Maximum acceptable downtime after a disaster', 'option_b': 'Maximum acceptable data loss measured in time', 'option_c': 'Minimum time to restore from backup', 'option_d': 'Maximum number of failed components tolerated',
                         'correct_answer': 'B', 'explanation': 'RPO (Recovery Point Objective) defines how much data loss is acceptable, measured in time. An RPO of 1 hour means your backup strategy must ensure data can be recovered to a point no more than 1 hour before the disaster.'},
                        {'question_text': 'EBS Snapshots are stored in which AWS service?',
                         'option_a': 'EFS', 'option_b': 'Glacier', 'option_c': 'S3', 'option_d': 'EBS itself',
                         'correct_answer': 'C', 'explanation': 'EBS Snapshots are stored in Amazon S3 (managed by AWS, not visible in your S3 console). Snapshots are incremental -- only blocks changed since the last snapshot are saved, reducing storage costs and backup time.'},
                        {'question_text': 'When restoring an RDS database from a snapshot, what is created?',
                         'option_a': 'The original DB instance is overwritten', 'option_b': 'A new DB instance with a new endpoint', 'option_c': 'A Read Replica of the original instance', 'option_d': 'An in-place restore with the same endpoint',
                         'correct_answer': 'B', 'explanation': 'RDS restore always creates a NEW DB instance with a new endpoint. You cannot restore to the same instance. After restoring, you must update your application connection strings to point to the new endpoint.'},
                        {'question_text': 'Which AWS Backup feature prevents backup deletion for a defined retention period to meet compliance requirements?',
                         'option_a': 'Backup Vault', 'option_b': 'Backup Plan', 'option_c': 'Vault Lock (WORM)', 'option_d': 'Cross-account backup',
                         'correct_answer': 'C', 'explanation': 'AWS Backup Vault Lock implements WORM (Write Once, Read Many) protection. Once enabled, no one -- including the root account -- can delete recovery points within the lock period, meeting SEC, FINRA, and CFTC compliance requirements.'},
                    ]
                },
                {
                    'title': 'Security, Compliance, and Cost Management',
                    'description': 'IAM advanced, GuardDuty, Security Hub, Trusted Advisor, and cost tools.',
                    'order_index': 3, 'points': 75, 'icon': '💰',
                    'sections': [
                        {'title': 'Security Services for SysOps',
                         'content': '<h4>Amazon GuardDuty</h4><p>Intelligent threat detection service that analyses CloudTrail logs, VPC Flow Logs, and DNS logs to identify threats. Detects: account compromise (unusual API calls, impossible travel), instance compromise (crypto mining, C&C traffic), bucket compromise (unusual S3 data access patterns). Findings are prioritised by severity. Integrates with Security Hub and EventBridge for automated response.</p><h4>AWS Security Hub</h4><p>Centralised security posture management. Aggregates findings from GuardDuty, Inspector, Macie, IAM Access Analyser, Firewall Manager, and third-party tools. Security standards checks: CIS AWS Foundations Benchmark, AWS Foundational Security Best Practices, PCI DSS. Security score tracks overall compliance posture.</p><h4>IAM Advanced</h4><p>IAM Access Analyser identifies resources shared outside your organisation. Service Control Policies (SCPs) in AWS Organisations set maximum permissions across accounts (do not grant permissions -- only restrict). Permission Boundaries set maximum permissions for IAM entities. IAM roles are preferred over long-term access keys. Enable MFA for root and all IAM users.</p>',
                         'order_index': 1, 'section_type': 'lesson'},
                        {'title': 'Cost Management and Optimisation',
                         'content': '<h4>AWS Cost Explorer</h4><p>Visualise, understand, and manage AWS costs and usage. Filter by service, region, account, tag, and usage type. Rightsizing recommendations identify over-provisioned EC2 and RDS instances. Cost anomaly detection uses ML to identify unusual spending patterns and alerts via SNS.</p><h4>AWS Budgets</h4><p>Set custom cost and usage budgets with alerts when thresholds are exceeded or forecasted to be exceeded. Budget types: Cost Budget, Usage Budget, RI Utilisation/Coverage Budget, Savings Plan Utilisation/Coverage Budget. Budget Actions automatically apply IAM policies or SCPs when budgets are exceeded.</p><h4>AWS Trusted Advisor</h4><p>Real-time guidance across five categories: Cost Optimisation (idle resources, underutilised EBS volumes), Performance (high-utilisation EC2, CloudFront optimisations), Security (open security groups, MFA on root, S3 bucket permissions), Fault Tolerance (EBS snapshots, RDS Multi-AZ), Service Limits (approaching service quotas). Business and Enterprise support plans unlock all checks.</p>',
                         'order_index': 2, 'section_type': 'lesson'},
                    ],
                    'questions': [
                        {'question_text': 'Amazon GuardDuty analyses which data sources to detect threats?',
                         'option_a': 'CloudWatch metrics and EC2 performance data', 'option_b': 'CloudTrail logs, VPC Flow Logs, and DNS logs', 'option_c': 'Config rules and compliance reports', 'option_d': 'S3 access logs and Lambda invocation logs',
                         'correct_answer': 'B', 'explanation': 'GuardDuty analyses CloudTrail management and data events, VPC Flow Logs, and DNS query logs to detect threats such as crypto mining, credential compromise, unusual API calls, and malicious IP communication.'},
                        {'question_text': 'Service Control Policies (SCPs) in AWS Organisations do which of the following?',
                         'option_a': 'Grant permissions to IAM users in member accounts', 'option_b': 'Set maximum permissions that can be granted within an account', 'option_c': 'Override IAM deny policies', 'option_d': 'Provide billing access to management accounts',
                         'correct_answer': 'B', 'explanation': 'SCPs set the maximum permissions available in member accounts but do not grant permissions. An action must be allowed by both an SCP and an IAM policy to be permitted. SCPs do not affect the management account.'},
                        {'question_text': 'Which AWS service identifies resources that are shared outside your AWS organisation or account?',
                         'option_a': 'GuardDuty', 'option_b': 'Security Hub', 'option_c': 'IAM Access Analyser', 'option_d': 'AWS Config',
                         'correct_answer': 'C', 'explanation': 'IAM Access Analyser uses logic-based analysis to identify resources (S3 buckets, IAM roles, KMS keys, Lambda functions, SQS queues) that are shared with external principals outside your zone of trust.'},
                        {'question_text': 'Which Trusted Advisor category checks for open inbound security group rules and missing MFA on root?',
                         'option_a': 'Cost Optimisation', 'option_b': 'Performance', 'option_c': 'Security', 'option_d': 'Service Limits',
                         'correct_answer': 'C', 'explanation': 'The Trusted Advisor Security category checks for common security vulnerabilities including unrestricted security group rules (0.0.0.0/0), missing MFA on root account, S3 bucket permissions, and IAM use (at least one IAM user required).'},
                        {'question_text': 'AWS Budgets Actions can automatically apply which controls when a budget threshold is breached?',
                         'option_a': 'Terminate EC2 instances over budget', 'option_b': 'Apply IAM policies or SCPs to restrict further spending', 'option_c': 'Disable the AWS account', 'option_d': 'Convert On-Demand to Reserved Instances automatically',
                         'correct_answer': 'B', 'explanation': 'Budget Actions automatically apply IAM policies (to deny access to services) or SCPs (to restrict actions in member accounts) when budget thresholds are breached, preventing runaway spending without manual intervention.'},
                    ]
                }
            ]
        }
    ]

    for path_data in paths_to_add:
        if path_data['slug'] in existing_slugs:
            continue

        path = LearningPath(
            slug=path_data['slug'], title=path_data['title'],
            subtitle=path_data['subtitle'], description=path_data['description'],
            difficulty=path_data['difficulty'], estimated_hours=path_data['estimated_hours'],
            total_points=path_data['total_points'], icon=path_data['icon']
        )
        db.session.add(path)
        db.session.flush()

        for mod_data in path_data['modules']:
            mod = PathModule(
                path_id=path.id, title=mod_data['title'], description=mod_data['description'],
                order_index=mod_data['order_index'], points=mod_data['points'], icon=mod_data['icon']
            )
            db.session.add(mod)
            db.session.flush()

            for i, sec in enumerate(mod_data.get('sections', []), 1):
                db.session.add(ModuleSection(
                    module_id=mod.id, title=sec['title'], content=sec['content'],
                    order_index=sec['order_index'], section_type=sec['section_type']
                ))

            for q in mod_data.get('questions', []):
                db.session.add(QuizQuestion(
                    module_id=mod.id, question_text=q['question_text'],
                    option_a=q['option_a'], option_b=q['option_b'],
                    option_c=q['option_c'], option_d=q['option_d'],
                    correct_answer=q['correct_answer'], explanation=q['explanation']
                ))

    db.session.commit()
    new_count = sum(1 for p in paths_to_add if p['slug'] not in existing_slugs)
    if new_count:
        print(f"Seeded {new_count} new AWS associate learning paths.")
