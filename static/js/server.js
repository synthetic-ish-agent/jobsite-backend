const express = require('express');
const cors = require('cors');
const path = require('path');
const app = express();
const port = 3000; // Assuming your frontend is on a different port

app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public'))); // Serve static files from the 'public' directory

const jobs = [
    {
        id: 1,
        title: 'Software Engineer',
        company: 'Tech Innovations Inc.',
        location: 'Lagos, Nigeria',
        description: 'Seeking a talented software engineer with experience in JavaScript, React, and Node.js. You will be responsible for developing and maintaining our web applications.',
        applyUrl: '#',
        responsibilities: [
            'Develop and maintain web applications using JavaScript frameworks.',
            'Collaborate with cross-functional teams to define, design, and ship new features.',
            'Write clean, maintainable, and well-documented code.',
            'Participate in code reviews.'
        ],
        requirements: [
            'Bachelor\'s degree in Computer Science or related field.',
            '3+ years of experience in software development.',
            'Strong proficiency in JavaScript, React, and Node.js.',
            'Experience with RESTful APIs.',
            'Familiarity with version control systems (Git).'
        ],
        benefits: ['Health insurance', 'Paid time off', 'Professional development opportunities']
    },
    {
        id: 2,
        title: 'Marketing Manager',
        company: 'Global Marketing Solutions',
        location: 'Abuja, Nigeria',
        description: 'Looking for a creative and driven marketing manager to lead our marketing campaigns and strategies.',
        applyUrl: '#',
        responsibilities: [
            'Develop and execute marketing strategies and campaigns.',
            'Manage and allocate marketing budgets.',
            'Oversee digital marketing efforts (SEO, SEM, social media).',
            'Analyze campaign performance and make recommendations for optimization.'
        ],
        requirements: [
            'Bachelor\'s degree in Marketing or related field.',
            '5+ years of experience in marketing management.',
            'Proven track record of successful marketing campaigns.',
            'Strong understanding of digital marketing trends.',
            'Excellent communication and leadership skills.'
        ],
        benefits: ['Competitive salary', 'Performance-based bonuses', 'Company car']
    },
    {
        id: 3,
        title: 'Frontend Developer',
        company: 'Web Wizards Ltd',
        location: 'Lagos, Nigeria',
        description: 'Exciting opportunity for a frontend developer proficient in Vue.js and modern UI/UX principles.',
        applyUrl: '#',
        responsibilities: [
            'Develop user interfaces using Vue.js.',
            'Collaborate with designers to implement UI/UX designs.',
            'Ensure the technical feasibility of UI/UX designs.',
            'Optimize applications for maximum speed and scalability.'
        ],
        requirements: [
            'Bachelor\'s degree in Computer Science or related field.',
            '2+ years of experience in frontend development.',
            'Strong proficiency in Vue.js, HTML, CSS, and JavaScript.',
            'Experience with responsive design principles.',
            'Familiarity with frontend build tools.'
        ],
        benefits: ['Flexible work hours', 'Remote work options', 'Training programs']
    },
    {
        id: 4,
        title: 'Data Analyst',
        company: 'Analytics Pro',
        location: 'Port Harcourt, Nigeria',
        description: 'We are hiring a data analyst with strong statistical skills and experience in data visualization tools.',
        applyUrl: '#',
        responsibilities: [
            'Collect, clean, and analyze data to identify trends and insights.',
            'Develop and maintain data reports and dashboards.',
            'Present findings to stakeholders.',
            'Collaborate with other teams to understand their data needs.'
        ],
        requirements: [
            'Bachelor\'s degree in Statistics, Mathematics, Computer Science, or related field.',
            '3+ years of experience in data analysis.',
            'Strong statistical skills and knowledge of data analysis techniques.',
            'Proficiency in data visualization tools (e.g., Tableau, Power BI).',
            'Experience with SQL.'
        ],
        benefits: ['Generous vacation policy', 'Employee discounts', 'Team-building activities']
    }
];

app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'login.html'));
});

app.get('/api/jobs/search', (req, res) => {
    const query = req.query.q ? req.query.q.toLowerCase() : '';
    if (!query) {
        return res.json(jobs);
    }
    const results = jobs.filter(job =>
        job.title.toLowerCase().includes(query) ||
        job.company.toLowerCase().includes(query) ||
        job.location.toLowerCase().includes(query) ||
        job.description.toLowerCase().includes(query)
    );
    res.json(results);
});

app.get('/api/jobs', (req, res) => {
    res.json(jobs);
});

app.get('/api/jobs/:id', (req, res) => {
    const jobId = parseInt(req.params.id);
    const job = jobs.find(j => j.id === jobId);
    if (job) {
        res.json(job);
    } else {
        res.status(404).json({ message: 'Job not found' });
    }
});

app.listen(port, () => {
    console.log('Server listening at http://localhost:' + port);
});