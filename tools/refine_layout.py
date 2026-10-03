"""Replace PDF-positioned letter fragments with semantic, editable HTML blocks.

This is the initial layout migration. Future copy edits belong in index.html.
"""
from pathlib import Path
from lxml import etree as ET
from extract_brochure import world_matrix, contours, bounds, NS

ROOT=Path(__file__).resolve().parents[1]


def placed(x,y,w,content,classes='',color=None):
    style=f'--x:{x}px;--y:{y}px;--w:{w}px'
    if color:style+=f';color:{color}'
    return f'<div class="placed {classes}" style="{style}">{content}</div>'


def listing(items):
    return '<ul class="course-list">'+''.join(f'<li>{item}</li>' for item in items)+'</ul>'


def project(x,y,w,semester,title,text,dark=False):
    return placed(x,y,w,f'<p class="eyebrow {"lime" if dark else "crimson"}">Semester {semester}</p><h4 class="project-title">{title}</h4><p class="body-copy">{text}</p>','project'+(' on-dark' if dark else ''))


def caption(x,y,w,name,detail):
    return placed(x,y,w,f'<p class="caption-name">{name}</p><p class="caption-detail">{detail}</p>','photo-caption on-dark')


def main():
    pages={}
    pages[1]=placed(141,870,1200,'<h1 class="cover-title">Industry Focused Business<br>&amp; Tech School,<span class="cover-tagline lime">Where You Graduate With Experience</span></h1>','on-dark')+placed(120,1878,1245,'''
      <div class="cover-facts">
        <div><p class="fact-label crimson">Duration</p><p class="fact-value">3 years<br>2027–2030</p></div>
        <div><p class="fact-label crimson">Eligibility</p><p class="fact-value">Class XII passouts,<br>all streams</p></div>
        <div><p class="fact-label crimson">Campus</p><p class="fact-value">Siliguri<br>Campus</p></div>
      </div>''','on-dark')

    pages[2]=placed(120,105,780,'<h1 class="display-title">Three-Year<br><em class="crimson">Undergraduate<br>Courses</em></h1>')
    pages[2]+=placed(1030,180,320,'<p class="seat-label">Made for</p><p class="seat-number crimson">40</p><p class="seat-label">Exclusive students<br>per course</p>','seat-badge on-dark')
    courses=[('01','UG in Business<br>Management','Learn management, finance, and marketing by building your own business. Intern from year one and graduate with real industry experience.'),('02','<span>UG in Digital Marketing</span><br>&amp; Commerce','Build and market your own D2C brand while learning digital marketing, e-commerce, and quick commerce. Intern from year one and graduate industry ready.'),('03','UG in Computer<br>Science &amp; AI','Build real tech products, master AI and emerging technologies, and intern from year one. Graduate ready for a career in tech.')]
    pages[2]+=placed(120,530,1245,'<div class="overview-grid">'+''.join(f'<article class="overview-course"><p class="course-index crimson">{n}</p><h3 class="{"course-title-marketing" if n=="02" else ""}">{title}</h3><p class="compact-copy">{copy}</p></article>' for n,title,copy in courses)+'</div>')
    pages[2]+=placed(170,1092,1190,'<h2 class="panel-intro">Built by the alumni of</h2><p class="alumni-title lime"><em>India’s top colleges</em></p>','on-dark')
    for x,name,role,education in [(198,'Ritesh Agarwal','Tech leader &amp; Startup founder',['MBA, IIM Bangalore','B.Tech, IIT Bombay','Ex Consultant at ITC &amp; BCG']),(806,'Aman Choudhury','Educationist &amp; Business leader',['MBA, ISB Hyderabad','B.Com Hons., SRCC Delhi','Ex Consultant at ZS &amp; EY'])]:
        pages[2]+=placed(x+24,1418,500,f'<p class="founder-label">Founder</p><p class="founder-role">{role}</p>','on-dark')
        pages[2]+=placed(x,1520,490,'<div class="credential-stack">'+''.join(f'<p>{s}</p>' for s in education)+'</div>','on-dark')
        pages[2]+=placed(x,1885,460,f'<p class="caption-name">{name}</p>','on-dark')
    pages[2]+=placed(0,1948,1485,'<h2 class="panel-intro centered">Our programs are backed by</h2>','backing-panel')

    pages[3]=placed(120,115,1245,'<p class="page-kicker crimson">Who Teaches You</p><h1 class="section-title">The Indian Industry Is<br><em class="crimson">Your Faculty</em></h1>')
    faculty=[('Sumit Sinhal','Founder, Kins Health'),('Prabin Agarwal','CEO, Prabin Agarwal'),('Madhu Jay','Head of Academics'),('LekhRam Nyoliwala','Renowned CA'),('Prejit Narayan','Ex CBO, Boat'),('Dhiraj Kothari','Founder, YOB Hotel Supplies'),('Neeraj Sancheti','Founder, Kreativ Street'),('Siddha Jain','CBO, Bombay Shaving Co.'),('Gaurav Garg','Engineering Manager, AWS'),('Kritika Choudhury','Co-Founder, GrapeLabs AI'),('Aryan Lohia','Co-Founder, AI Hive'),('Archit Agarwal','Project Owner, Regeneration Projects')]
    for i,(name,role) in enumerate(faculty):
        row,col=divmod(i,4)
        pages[3]+=placed([84,411,740,1068][col],[539,967,1380][row],300,f'<p class="faculty-name">{name}</p><p class="faculty-role">{role}</p>','faculty-caption')
    pages[3]+=placed(120,1830,1245,'<div class="faculty-stats">'+''.join(f'<div><span class="stat-number crimson">{n}</span><p>{label}</p></div>' for n,label in [('35%','Visiting<br>Faculty'),('35%','Resident<br>Faculty'),('30%','Industry<br>Masterclass')])+'</div>')
    pages[3]+=placed(120,2035,1245,'<p class="annual-masterclasses"><span class="lime">60+ masterclasses</span> conducted in a year</p>','on-dark')

    pages[4]=placed(120,128,1245,'<h1 class="curriculum-title"><span>The 3-year of</span><em class="crimson">Business Curriculum</em></h1>')
    pages[4]+=placed(120,435,1245,'<div class="programme-title"><span class="programme-number crimson">01</span><h2>UG in Business <span class="crimson">Management</span></h2></div>')
    pages[4]+=placed(120,610,590,'<span class="tag tag-dark">INCLASS</span>')+placed(790,610,575,'<span class="tag tag-lime">OUTCLASS</span>')
    pages[4]+=placed(120,713,595,'<span class="tag tag-crimson">Core Courses</span>')
    pages[4]+=placed(120,790,595,listing(['Marketing 101','Fundamentals of Accounting','Foundation of HRM','Business Economics (Micro &amp; Macro)','Business Strategy and Decision Making','Corporate Accounting','Sales and Advanced Marketing (GTM)','Corporate Finance','Data Analytics (Excel, Power BI)','Entrepreneurship','Digital Marketing and E-commerce','Product Management']))
    pages[4]+=placed(120,1285,595,'<span class="tag tag-crimson">Everyday Courses</span>')
    pages[4]+=placed(120,1363,595,listing(['AI in Business','Art of Communication','Financial Markets Fundamentals','International Business: Imports and Exports','Business Automation &amp; Systems','LinkedIn for Growth','Project Management','Data Analytics (Excel, Power BI)']))
    consulting='Work with start-ups, dealerships, and local businesses to improve their strategy, helping them grow their revenue &amp; profits.'
    for sem,y,title in [(1,710,'Local Business Consulting'),(2,1150,'Drop Shipping'),(3,1600,'AI Powered Hackathons')]:pages[4]+=project(790,y,575,sem,title,consulting)

    pages[5]=placed(120,105,650,'<div class="programme-title stacked"><span class="programme-number crimson">02</span><h2>UG in Digital<br>Marketing &amp;<br><span class="crimson">Commerce</span></h2></div>')
    pages[5]+=placed(120,354,630,'<span class="tag tag-dark">INCLASS</span>')+placed(850,125,515,'<span class="tag tag-lime">OUTCLASS</span>')
    pages[5]+=placed(120,425,630,'<span class="tag tag-crimson">Core Courses</span>')
    pages[5]+=placed(120,500,630,listing(['Principles of Marketing &amp; Consumer Behaviour','Financial Accounting','Social Media Marketing','Advanced Digital Marketing','E-Commerce and Quick Commerce Economy','Performance Marketing (SEO, Meta Ads, Google Ads)','Strategic Brand Management','Growth Hacking']))
    pages[5]+=placed(120,873,630,'<span class="tag tag-crimson">Everyday Courses</span>')
    pages[5]+=placed(120,950,630,listing(['AI in Marketing','Art of Communication','Financial Markets Fundamentals','Design and No-Code','Creative Production']))
    for sem,y,title,copy in [(1,220,'You Build a Brand from Scratch','Turn a business idea into a brand and launch it in the real market.'),(2,440,'You Become a Digital Creator','Create content, build your portfolio, and grow a real audience.'),(3,670,'You Intern at a Marketing Agency','Work on live campaigns with real budgets for real clients and brands.')]:pages[5]+=project(850,y,515,sem,title,copy)
    pages[5]+=placed(120,1205,650,'<div class="programme-title stacked"><span class="programme-number lime">03</span><h2>UG in Computer<br>Science &amp; AI</h2></div>','on-dark')
    pages[5]+=placed(120,1372,630,'<span class="tag tag-white">INCLASS</span>')+placed(850,1240,515,'<span class="tag tag-lime">OUTCLASS</span>')
    pages[5]+=placed(120,1450,630,'<span class="tag tag-lime">Core Courses</span>')
    pages[5]+=placed(120,1530,630,listing(['Programming Foundations with Python','Web Foundations (HTML, CSS, JavaScript)','Databases and Back end Basics','Applied AI: Working with LLMs','Full-Stack Development','AI Automation and Agents for Business','Mobile Application Development']),'on-dark')
    pages[5]+=placed(120,1841,630,'<span class="tag tag-lime">Everyday Courses</span>')
    pages[5]+=placed(120,1920,630,listing(['Business Communication','The Digital Workbench','Design and No Code','Product Management','Personal and Business Finance']),'on-dark')
    for sem,y,title,copy in [(1,1340,'You Build a Live Website','Build and deploy a live website for a real local business, with client sign-off.'),(2,1590,'You Deploy a Full Stack Application','Build and deploy a full-stack app with an AI feature and at least 10 real users.'),(3,1850,'You Create AI Agentic Solutions for Companies','Build and deploy AI agents that solve real business problems.')]:pages[5]+=project(850,y,515,sem,title,copy,True)

    pages[6]=placed(120,145,1245,'<h1 class="internship-title">Do 3 Internships <em class="crimson">in 3 Years</em></h1>')
    for args in [(690,476,330,'Pranay Shah','ShUtuP Marketing, Mumbai'),(1080,476,280,'Krish Agarwal','Doodhvale Farms, Delhi'),(690,752,330,'Mayank Garg','Stratwings, Siliguri'),(1080,752,280,'Viviana Lama','Wownooks, Siliguri'),(120,760,480,'Chirag Agrahari','TEFL, Ireland'),(120,1040,285,'Nand Kumar','Sona Wheels, Siliguri'),(444,1040,295,'Vaibhav Agarwal','Kamac Engineers, Siliguri'),(777,1040,290,'Nishi Agarwal','Tata Motors, Siliguri'),(1110,1040,265,'Aisha Thapa','Cook &amp; Serve, Siliguri')]:pages[6]+=caption(*args)
    pages[6]+=placed(120,1135,1245,'<h2 class="brand-tagline">Earn by working <em class="crimson">with 75+ brands</em></h2>')
    pages[6]+=placed(790,1413,575,'<h2 class="small-section-title crimson">National Achievements</h2>')
    pages[6]+=placed(450,1455,255,'<h3 class="profile-title">Daiwik<br><span class="crimson">Bansal</span></h3><p class="profile-label">Project Name</p>')
    pages[6]+=placed(120,1795,565,'<p class="body-copy">NEX Venture Lab is our in-house startup incubation centre, home to BYOB (Build Your Own Business), where you’re funded and mentored by investors as you build your own venture.</p>')
    for y,name,copy in [(1536,'Shaswat Goyal','Intern at ITC Foods'),(1748,'Avneesh Agarwal','U-19 Cricket Trials, Sikkim'),(1955,'Daiwik &amp; Harman','Top 18 National Finalists<br>BBIC 2.0')]:pages[6]+=placed(1020,y,330,f'<p class="achievement-name">{name}</p><p class="achievement-detail">{copy}</p>')

    pages[7]=placed(120,107,1245,'<p class="page-kicker crimson">Campus Life</p><h1 class="campus-title">Student Life <span class="crimson">at NEXIS</span></h1>','on-dark')
    for x,y,text in [(278,645,'PVR Inox, ML Acropolis'),(646,645,'Beaumonde, Siliguri'),(1009,645,'Cogito Digital, Siliguri'),(120,1022,'Speakathon'),(484,1022,'Investment Hackathon'),(850,1022,'Yeh Dil hai Muskil'),(300,1407,'Cricket'),(665,1407,'Basketball'),(1030,1407,'Badminton'),(124,1785,'PitchTank'),(494,1785,'NEXMun'),(860,1785,'BIZNEX')]:pages[7]+=placed(x,y,310,f'<p>{text}</p>','activity-caption on-dark')
    for x,y,text,dark in [(132,710,'Industry Visit',False),(1230,1093,'Hackathons',True),(150,1465,'Sports Showdown',False),(1245,1850,'Mega Fests',True)]:pages[7]+=f'<div class="vertical-label {"" if dark else "on-dark"}" style="--x:{x}px;--y:{y}px">{text}</div>'
    pages[7]+=placed(180,1955,1150,'<p class="body-copy">A corporate-style campus at the heart of Siliguri, where you’ll make lifelong memories, compete, organise events, celebrate festivals, and make the most of every moment.</p>','on-dark')

    pages[8]=placed(120,125,800,'<h1 class="degree-title"><em>Degree &amp;<br><span class="crimson">Certification</span></em></h1>','on-dark')
    pages[8]+=placed(120,418,720,'''
      <div class="degree-copy body-copy">
        <p>On completion of the 3 year Program, students are awarded a Professional Certificate for the Undergraduate Programme in Business Management by NEXIS School of Business.</p>
        <p>Students are advised to enroll in a UGC-recognized online Bachelor’s Degree in Business Administration (BBA) from a reputed private university. This provides greater career flexibility to the students.</p>
        <p>As per UGC regulations, online degrees are completely equivalent to those gained through traditional, in-person programs.</p>
      </div>''','on-dark')
    pages[8]+='''
      <section class="admissions-panel">
        <h2 class="admissions-title"><span class="crimson">Admission</span> Process</h2>
        <p class="admissions-intro">Only 40 exclusive students will be selected per course.</p>
        <div class="admissions-grid">
          <article class="admission-card">
            <p class="admission-number crimson">01</p><p class="eyebrow crimson">Apply</p>
            <h3>Complete the<br>Application Online</h3>
            <p>Share your academic and extracurricular credentials and pay the application fee.</p>
          </article>
          <article class="admission-card">
            <p class="admission-number crimson">02</p><p class="eyebrow crimson">Test</p>
            <h3>Take the NexGen<br>Aptitude Test</h3>
            <p>Students take a 45-minute aptitude test that judges their analytical &amp; logical reasoning abilities.</p>
          </article>
          <article class="admission-card">
            <p class="admission-number crimson">03</p><p class="eyebrow crimson">Meet</p>
            <h3>Interview and<br>Admission Decision</h3>
            <p>1:1 interview with the admissions committee. After the interview, results will be declared within 10 days.</p>
          </article>
        </div>
      </section>
      <footer class="contact-panel on-dark">
        <h2>Get in Touch</h2>
        <div class="contact-grid">
          <div class="contact-stack">
            <div><h3>Email</h3><p><a href="mailto:info@nexisschool.com">info@nexisschool.com</a></p></div>
            <div><h3>Phone</h3><p><a href="tel:+919733124000">+91 9733124000</a><br><a href="tel:+919733127000">+91 9733127000</a></p></div>
          </div>
          <div class="contact-stack">
            <div><h3>Website</h3><p><a href="https://www.nexisschool.com">www.nexisschool.com</a></p></div>
            <div><h3>Address</h3><p>5th Floor, Tradium Building<br>Sevoke Road, Siliguri</p></div>
          </div>
        </div>
        <h2 class="follow-title">Follow Us</h2>
        <div class="social-row"><span><b aria-hidden="true">◎</b> nexis.school</span><span><b aria-hidden="true">f</b> nexisschool</span><span><b aria-hidden="true">in</b> nexisschoolofbusiness</span></div>
      </footer>'''

    doc=ET.parse(str(ROOT/'index.html'),ET.HTMLParser())
    for section in doc.xpath('//section[@data-page]'):
        pi=int(section.get('data-page'))
        layer=section.find('.//div[@class="text-layer"]')
        layer.set('class','brochure-copy')
        for el in list(layer):layer.remove(el)
        fragment=ET.fromstring(f'<div>{pages[pi]}</div>',ET.HTMLParser())
        for el in fragment.find('body/div'):layer.append(el)
    (ROOT/'index.html').write_bytes(ET.tostring(doc,encoding='utf-8',method='html',doctype='<!doctype html>',pretty_print=True))
    # Native HTML tags and lists replace the original backgrounds and bullets.
    for pi in [2,4,5]:
        path=ROOT/'assets/artwork'/f'page-{pi:02}.svg'
        svg=ET.parse(str(path))
        for el in svg.xpath('.//s:path[not(ancestor::s:defs)]',namespaces=NS):
            parts=contours(el.get('d'),world_matrix(el))
            boxes=[b for part in parts if (b:=bounds(part))]
            if not boxes:continue
            x1=min(b[0] for b in boxes);y1=min(b[1] for b in boxes);x2=max(b[2] for b in boxes);y2=max(b[3] for b in boxes)
            w=x2-x1;h=y2-y1
            remove=False
            if pi==2 and y1>500 and y2<1100 and h>450 and w>1200:remove=True
            if pi in [4,5]:
                if 180<w<440 and 40<h<80 and 80<x1<1100:remove=True
                if x1<180 and x2<200 and y1>400 and h>100:remove=True
            if remove:el.getparent().remove(el)
        path.write_bytes(ET.tostring(svg,encoding='utf-8',xml_declaration=True))
    print('Rebuilt all eight text layers with semantic HTML, shared typography, and aligned margins.')


if __name__=='__main__':main()
