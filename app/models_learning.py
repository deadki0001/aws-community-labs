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
                        '<p>Cloud computing delivers computing services—servers, storage, databases, networking, software—'
                        'over the internet ("the cloud"). Instead of owning physical data centres, you rent access from '
                        'a cloud provider and pay only for what you use.</p>'
                        '<h4>Key Benefits</h4>'
                        '<ul>'
                        '<li><strong>Trade fixed expense for variable expense</strong> — pay only for what you consume.</li>'
                        '<li><strong>Benefit from massive economies of scale</strong> — providers aggregate usage from '
                        'hundreds of thousands of customers.</li>'
                        '<li><strong>Stop guessing capacity</strong> — scale up or down within minutes.</li>'
                        '<li><strong>Increase speed and agility</strong> — new resources available in seconds.</li>'
                        '<li><strong>Go global in minutes</strong> — deploy in multiple regions around the world.</li>'
                        '</ul>'
                        '<h4>Cloud Deployment Models</h4>'
                        '<ul>'
                        '<li><strong>Public Cloud</strong> — Resources owned and operated by a third-party provider, '
                        'delivered over the internet (e.g., AWS, Azure, GCP).</li>'
                        '<li><strong>Private Cloud</strong> — Cloud resources used exclusively by a single organisation, '
                        'hosted on-premises or by a third party.</li>'
                        '<li><strong>Hybrid Cloud</strong> — Combines public and private clouds, allowing data and '
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
                        'connectivity within a Region. AZs are physically separated—typically tens of miles apart—'
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
                    'explanation': 'IaaS provides virtualised compute, storage, and networking. You manage the OS, middleware, and applications — giving you the most control.'
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
                    'title': 'Amazon EC2 – Elastic Compute Cloud',
                    'content': (
                        '<p>Amazon EC2 provides resizable compute capacity in the cloud. It reduces the time '
                        'required to obtain and boot new server instances to minutes.</p>'
                        '<h4>Instance Types</h4>'
                        '<ul>'
                        '<li><strong>General Purpose</strong> (e.g., t3, m6i) — balanced compute, memory, networking.</li>'
                        '<li><strong>Compute Optimised</strong> (e.g., c6i) — high-performance processors; batch workloads.</li>'
                        '<li><strong>Memory Optimised</strong> (e.g., r6i) — fast performance for large in-memory datasets.</li>'
                        '<li><strong>Storage Optimised</strong> (e.g., i3) — high sequential read/write access to large datasets.</li>'
                        '</ul>'
                        '<h4>Purchasing Options</h4>'
                        '<ul>'
                        '<li><strong>On-Demand</strong> — pay by the second, no commitments.</li>'
                        '<li><strong>Reserved Instances</strong> — 1 or 3 year commitment, up to 72% savings.</li>'
                        '<li><strong>Spot Instances</strong> — bid on unused capacity, up to 90% savings (can be interrupted).</li>'
                        '<li><strong>Savings Plans</strong> — flexible pricing model, commit to a consistent usage amount.</li>'
                        '</ul>'
                    ),
                    'order_index': 1,
                    'section_type': 'lesson'
                },
                {
                    'title': 'Amazon S3 – Simple Storage Service',
                    'content': (
                        '<p>Amazon S3 is object storage built to store and retrieve any amount of data from '
                        'anywhere. It provides 99.999999999% (11 nines) durability.</p>'
                        '<h4>Storage Classes</h4>'
                        '<ul>'
                        '<li><strong>S3 Standard</strong> — frequently accessed data; low latency.</li>'
                        '<li><strong>S3 Standard-IA</strong> — infrequent access; lower cost, retrieval fee applies.</li>'
                        '<li><strong>S3 One Zone-IA</strong> — stored in single AZ; 20% cheaper than Standard-IA.</li>'
                        '<li><strong>S3 Glacier Instant Retrieval</strong> — archived data with millisecond retrieval.</li>'
                        '<li><strong>S3 Glacier Flexible Retrieval</strong> — minutes-to-hours retrieval; very low cost.</li>'
                        '<li><strong>S3 Glacier Deep Archive</strong> — lowest cost; 12-hour retrieval; long-term archive.</li>'
                        '</ul>'
                        '<h4>Key Concepts</h4>'
                        '<ul>'
                        '<li><strong>Buckets</strong> — containers for objects; globally unique names.</li>'
                        '<li><strong>Objects</strong> — files plus metadata; up to 5 TB each.</li>'
                        '<li><strong>Bucket Policies & ACLs</strong> — control access at bucket and object level.</li>'
                        '<li><strong>Versioning</strong> — keep multiple variants of an object in the same bucket.</li>'
                        '</ul>'
                    ),
                    'order_index': 2,
                    'section_type': 'lesson'
                },
                {
                    'title': 'IAM, VPC, RDS & Lambda',
                    'content': (
                        '<h4>AWS IAM – Identity and Access Management</h4>'
                        '<p>IAM lets you manage access to AWS services and resources. Key components: '
                        '<strong>Users</strong> (individual people/services), <strong>Groups</strong> (collection of users), '
                        '<strong>Roles</strong> (assumed by services/users for temporary access), '
                        '<strong>Policies</strong> (JSON documents defining permissions). '
                        'Best practice: grant least privilege.</p>'
                        '<h4>Amazon VPC – Virtual Private Cloud</h4>'
                        '<p>VPC lets you provision a logically isolated section of AWS Cloud. Key components: '
                        '<strong>Subnets</strong> (public/private), <strong>Route Tables</strong>, '
                        '<strong>Internet Gateway</strong> (connect VPC to internet), '
                        '<strong>NAT Gateway</strong> (allow private subnet instances to access internet), '
                        '<strong>Security Groups</strong> (stateful instance-level firewall), '
                        '<strong>Network ACLs</strong> (stateless subnet-level firewall).</p>'
                        '<h4>Amazon RDS – Relational Database Service</h4>'
                        '<p>Managed relational database service supporting MySQL, PostgreSQL, MariaDB, Oracle, '
                        'SQL Server, and Amazon Aurora. Handles: provisioning, patching, backup, recovery, '
                        'failover, and scaling.</p>'
                        '<h4>AWS Lambda</h4>'
                        '<p>Serverless compute — run code without provisioning or managing servers. Pay only '
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
                    'explanation': 'IAM Roles attached to EC2 instances provide temporary, automatically-rotated credentials — the best practice for granting AWS services access to other AWS services.'
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
                        '<li>Create individual IAM users — never share credentials.</li>'
                        '<li>Use groups to assign permissions to IAM users.</li>'
                        '<li>Grant least privilege — only permissions required to perform a task.</li>'
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
                        '<li><strong>AWS Shield Standard</strong> — automatically protects all AWS customers from '
                        'common DDoS attacks at no additional charge.</li>'
                        '<li><strong>AWS Shield Advanced</strong> — enhanced DDoS protection, 24/7 DDoS Response Team, '
                        'cost protection against scaling charges.</li>'
                        '<li><strong>AWS WAF</strong> — Web Application Firewall to protect against common web exploits '
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
                        '<li><strong>Pay as you go</strong> — pay for exactly what you use, when you use it.</li>'
                        '<li><strong>Pay less when you reserve</strong> — Reserved Instances and Savings Plans offer '
                        'significant discounts in exchange for a commitment.</li>'
                        '<li><strong>Pay less with volume-based discounts</strong> — the more you use, the less you pay '
                        'per unit (e.g., S3 tiered pricing).</li>'
                        '</ul>'
                        '<h4>AWS Free Tier</h4>'
                        '<p>Three types of free tier offers:</p>'
                        '<ul>'
                        '<li><strong>Always Free</strong> — never expires (e.g., AWS Lambda: 1M requests/month).</li>'
                        '<li><strong>12 Months Free</strong> — available for 12 months from sign-up '
                        '(e.g., EC2 t2.micro 750 hrs/month, S3 5 GB).</li>'
                        '<li><strong>Trials</strong> — short-term free trials for specific services.</li>'
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
                    'explanation': '"Pay less when you reserve" — Reserved Instances and Savings Plans offer up to 72% savings versus On-Demand in exchange for a 1 or 3 year commitment.'
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
                        '<li><strong>Operational Excellence</strong> — ability to run and monitor systems to deliver business value. '
                        'Key practices: Infrastructure as Code (CloudFormation), CI/CD pipelines, small reversible changes.</li>'
                        '<li><strong>Security</strong> — protecting information and systems. '
                        'Key practices: implement a strong identity foundation, enable traceability, apply security at all layers, automate security best practices, protect data in transit and at rest.</li>'
                        '<li><strong>Reliability</strong> — ability to recover from failures and dynamically acquire resources. '
                        'Key practices: test recovery procedures, automatically recover from failure, scale horizontally.</li>'
                        '<li><strong>Performance Efficiency</strong> — using computing resources efficiently. '
                        'Key practices: use serverless architectures, experiment more often, go global in minutes.</li>'
                        '<li><strong>Cost Optimisation</strong> — avoiding unnecessary costs. '
                        'Key practices: adopt a consumption model, measure overall efficiency, stop spending on undifferentiated heavy lifting.</li>'
                        '<li><strong>Sustainability</strong> — minimising environmental impacts. '
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
                        '<li><strong>Fault Tolerant</strong> — system continues to function even when components fail '
                        '(zero downtime); requires redundancy at every layer.</li>'
                        '<li><strong>Highly Available</strong> — system is designed to recover quickly from failure '
                        '(minimal downtime); uses redundancy but may have brief outages during failover.</li>'
                        '</ul>'
                        '<h4>Disaster Recovery Strategies</h4>'
                        '<ul>'
                        '<li><strong>Backup & Restore</strong> — cheapest; backup data to S3; longest RTO/RPO.</li>'
                        '<li><strong>Pilot Light</strong> — minimal version of environment always running; '
                        'scale up when needed.</li>'
                        '<li><strong>Warm Standby</strong> — scaled-down but fully functional version always running.</li>'
                        '<li><strong>Multi-Site Active/Active</strong> — most expensive; fastest recovery; '
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
                        '<li><strong>Hub</strong> — Layer 1; broadcasts all frames to all ports; half-duplex; obsolete.</li>'
                        '<li><strong>Switch</strong> — Layer 2; learns MAC addresses; forwards frames only to the correct port; '
                        'full-duplex; creates separate collision domains per port.</li>'
                        '<li><strong>Router</strong> — Layer 3; routes packets between different networks using IP addresses; '
                        'separates broadcast domains.</li>'
                        '<li><strong>Firewall</strong> — inspects and filters traffic based on rules; can be stateful or stateless.</li>'
                        '<li><strong>Wireless Access Point (WAP)</strong> — connects wireless clients to a wired network.</li>'
                        '</ul>'
                        '<h4>Ethernet Cable Types</h4>'
                        '<ul>'
                        '<li><strong>Straight-through</strong> — connects different device types (PC to switch, switch to router).</li>'
                        '<li><strong>Crossover</strong> — connects same device types (PC to PC, switch to switch). '
                        'Modern switches use Auto-MDIX to detect automatically.</li>'
                        '<li><strong>Fibre Optic</strong> — uses light; immune to EMI; longer distances. '
                        'Single-mode for long distances; multi-mode for shorter distances.</li>'
                        '</ul>'
                        '<h4>Network Topologies</h4>'
                        '<ul>'
                        '<li><strong>Star</strong> — all devices connect to a central switch (most common in LANs).</li>'
                        '<li><strong>Bus</strong> — all devices share a single cable (legacy).</li>'
                        '<li><strong>Ring</strong> — devices connect in a loop; Token Ring (legacy).</li>'
                        '<li><strong>Mesh</strong> — every device connected to every other device; high redundancy.</li>'
                        '</ul>'
                    ),
                    'order_index': 2,
                    'section_type': 'lesson'
                }
            ],
            'questions': [
                {
                    'question_text': 'At which OSI layer do switches operate?',
                    'option_a': 'Layer 1 – Physical',
                    'option_b': 'Layer 2 – Data Link',
                    'option_c': 'Layer 3 – Network',
                    'option_d': 'Layer 4 – Transport',
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
                        '<td style="padding:6px;border:1px solid rgba(255,255,255,0.2);">1.0.0.0 – 126.255.255.255</td>'
                        '<td style="padding:6px;border:1px solid rgba(255,255,255,0.2);">/8 (255.0.0.0)</td>'
                        '<td style="padding:6px;border:1px solid rgba(255,255,255,0.2);">Large networks</td></tr>'
                        '<tr><td style="padding:6px;border:1px solid rgba(255,255,255,0.2);">B</td>'
                        '<td style="padding:6px;border:1px solid rgba(255,255,255,0.2);">128.0.0.0 – 191.255.255.255</td>'
                        '<td style="padding:6px;border:1px solid rgba(255,255,255,0.2);">/16 (255.255.0.0)</td>'
                        '<td style="padding:6px;border:1px solid rgba(255,255,255,0.2);">Medium networks</td></tr>'
                        '<tr><td style="padding:6px;border:1px solid rgba(255,255,255,0.2);">C</td>'
                        '<td style="padding:6px;border:1px solid rgba(255,255,255,0.2);">192.0.0.0 – 223.255.255.255</td>'
                        '<td style="padding:6px;border:1px solid rgba(255,255,255,0.2);">/24 (255.255.255.0)</td>'
                        '<td style="padding:6px;border:1px solid rgba(255,255,255,0.2);">Small networks (up to 254 hosts)</td></tr>'
                        '</table>'
                        '<h4>Private IP Ranges (RFC 1918)</h4>'
                        '<ul>'
                        '<li>10.0.0.0/8 — Class A private range</li>'
                        '<li>172.16.0.0/12 — Class B private range (172.16.0.0 – 172.31.255.255)</li>'
                        '<li>192.168.0.0/16 — Class C private range</li>'
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
                        '<li><strong>Hosts per subnet</strong> = 2<sup>h</sup> – 2 where h = host bits '
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
                        '<li><strong>Learn</strong> — when a frame arrives, the switch records the source MAC '
                        'address and ingress port in its MAC address table (CAM table).</li>'
                        '<li><strong>Flood</strong> — if the destination MAC is unknown, the switch floods the '
                        'frame out all ports except the ingress port.</li>'
                        '<li><strong>Forward</strong> — if the destination MAC is known, the switch forwards '
                        'the frame only to the correct port.</li>'
                        '<li><strong>Filter</strong> — if source and destination are on the same port, the '
                        'frame is dropped.</li>'
                        '</ol>'
                        '<h4>Duplex & Speed</h4>'
                        '<ul>'
                        '<li><strong>Half-duplex</strong> — can only send or receive at one time (hubs, legacy).</li>'
                        '<li><strong>Full-duplex</strong> — can send and receive simultaneously; standard for '
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
                        '<li><strong>Access port</strong> — carries traffic for a single VLAN; connects end devices.</li>'
                        '<li><strong>Trunk port</strong> — carries traffic for multiple VLANs using 802.1Q tagging; '
                        'connects switches or routers.</li>'
                        '<li><strong>Native VLAN</strong> — the VLAN whose frames traverse a trunk untagged (default VLAN 1; '
                        'best practice: change to an unused VLAN).</li>'
                        '</ul>'
                        '<h4>802.1Q Trunking</h4>'
                        '<p>IEEE 802.1Q inserts a 4-byte tag into the Ethernet frame between the source MAC and '
                        'EtherType fields. The tag includes a 12-bit VLAN ID (VID), allowing 4,094 VLANs.</p>'
                        '<h4>Inter-VLAN Routing</h4>'
                        '<ul>'
                        '<li><strong>Router on a Stick</strong> — single router interface with sub-interfaces, '
                        'one per VLAN; trunk link between switch and router.</li>'
                        '<li><strong>Layer 3 Switch (SVI)</strong> — switch with IP routing capability; '
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
                        '<li><strong>Hello packets</strong> — discover and maintain neighbour relationships.</li>'
                        '<li><strong>LSA (Link State Advertisement)</strong> — carries topology information '
                        'flooded to all routers in the same OSPF area.</li>'
                        '<li><strong>LSDB (Link State Database)</strong> — each router maintains an identical '
                        'database of all LSAs in the area.</li>'
                        '<li><strong>DR/BDR</strong> — on multi-access networks, a Designated Router (DR) and '
                        'Backup DR (BDR) are elected to reduce OSPF traffic.</li>'
                        '<li><strong>Router ID</strong> — unique 32-bit number identifying each OSPF router; '
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
                    'explanation': 'Connected interfaces have an AD of 0 — the most trusted route source. Static routes are AD 1, OSPF is 110, RIP is 120.'
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
                    'option_c': 'Both routes — load balance',
                    'option_d': 'The most recently learned route',
                    'correct_answer': 'B',
                    'explanation': 'The router installs the route with the lowest Administrative Distance. OSPF (110) beats RIP (120) — lower AD = more trusted = preferred.'
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
                        '<li><strong>Standard ACLs</strong> (numbered 1–99, 1300–1999) — filter by source IP only. '
                        'Place as close to the destination as possible.</li>'
                        '<li><strong>Extended ACLs</strong> (numbered 100–199, 2000–2699) — filter by source IP, '
                        'destination IP, protocol, and port. Place as close to the source as possible.</li>'
                        '</ul>'
                        '<h4>ACL Placement</h4>'
                        '<ul>'
                        '<li><strong>Inbound</strong> — applied before the routing decision; more efficient.</li>'
                        '<li><strong>Outbound</strong> — applied after the routing decision.</li>'
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
                        '<li><strong>Static NAT</strong> — one-to-one mapping of private to public IP; used for servers.</li>'
                        '<li><strong>Dynamic NAT</strong> — maps private IPs to a pool of public IPs; no port translation.</li>'
                        '<li><strong>PAT / NAT Overload</strong> — many-to-one; maps multiple private IPs to a single '
                        'public IP using unique port numbers. Most common — used in home routers.</li>'
                        '</ul>'
                        '<h4>Network Automation & Programmability</h4>'
                        '<p>Modern networks use automation to improve consistency and reduce human error. Key concepts:</p>'
                        '<ul>'
                        '<li><strong>SDN (Software-Defined Networking)</strong> — separates the control plane from the '
                        'data plane. A centralised controller manages the network.</li>'
                        '<li><strong>REST APIs</strong> — HTTP-based APIs used by network controllers (e.g., Cisco DNA '
                        'Centre) to communicate with devices. Use JSON or XML data formats.</li>'
                        '<li><strong>Ansible</strong> — agentless automation tool; uses YAML playbooks; ideal for '
                        'network configuration management.</li>'
                        '<li><strong>Python</strong> — widely used for network automation scripts; libraries: '
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
                    'explanation': 'PAT (Port Address Translation), also called NAT Overload, maps many private IPs to one public IP by tracking sessions using unique source port numbers — used in most home and office routers.'
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
                    'explanation': 'Ansible is agentless (uses SSH/NETCONF — no software needed on managed devices), uses YAML playbooks, and is widely adopted for network automation.'
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
