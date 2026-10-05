<div align="left">
  <svg width="720" height="120" viewBox="0 0 720 120" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Hi, I'm Tejas">
    <defs>
      <linearGradient id="matrixGradient" x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%" stop-color="#00ff41">
          <animate attributeName="stop-color" values="#00ff41;#0eff00;#00ff41" dur="4s" repeatCount="indefinite"/>
        </stop>
        <stop offset="50%" stop-color="#0eff00">
          <animate attributeName="stop-color" values="#0eff00;#00ff41;#0eff00" dur="4s" repeatCount="indefinite"/>
        </stop>
        <stop offset="100%" stop-color="#39ff14">
          <animate attributeName="stop-color" values="#39ff14;#00ff41;#39ff14" dur="4s" repeatCount="indefinite"/>
        </stop>
      </linearGradient>

      <filter id="matrixGlow" x="-50%" y="-50%" width="200%" height="200%">
        <feGaussianBlur stdDeviation="3.5" result="coloredBlur"/>
        <feMerge>
          <feMergeNode in="coloredBlur"/>
          <feMergeNode in="coloredBlur"/>
          <feMergeNode in="SourceGraphic"/>
        </feMerge>
      </filter>

      <filter id="shadowGlow">
        <feGaussianBlur stdDeviation="4" result="blur"/>
        <feComponentTransfer>
          <feFuncA type="linear" slope="0.5"/>
        </feComponentTransfer>
        <feMerge>
          <feMergeNode in="blur"/>
          <feMergeNode in="SourceGraphic"/>
        </feMerge>
      </filter>

      <style>
        @keyframes matrixFlicker {
          0%, 100% { opacity: 1; text-shadow: 0 0 10px #00ff41, 0 0 20px #00ff41, 0 0 30px #00ff41; }
          4% { opacity: 0.95; text-shadow: 0 0 12px #00ff41, 0 0 22px #00ff41, 0 0 32px #00ff41; }
          8% { opacity: 1; text-shadow: 0 0 10px #00ff41, 0 0 20px #00ff41, 0 0 30px #00ff41; }
          12% { opacity: 0.92; text-shadow: 0 0 11px #00ff41, 0 0 21px #00ff41, 0 0 31px #00ff41; }
          16% { opacity: 1; text-shadow: 0 0 10px #00ff41, 0 0 20px #00ff41, 0 0 30px #00ff41; }
          20% { opacity: 0.98; text-shadow: 0 0 10px #00ff41, 0 0 20px #00ff41, 0 0 30px #00ff41; }
        }
        
        #matrixText {
          animation: matrixFlicker 6s infinite;
          font-family: 'Courier New', monospace;
        }

        @keyframes fadeGlow {
          0%, 100% { opacity: 0.6; }
          50% { opacity: 1; }
        }

        #underline {
          animation: fadeGlow 3s ease-in-out infinite;
        }
      </style>
    </defs>

    <!-- Outer glow layer -->
    <rect x="5" y="15" width="710" height="85" rx="8" fill="none" stroke="#00ff41" stroke-width="2" opacity="0.3" filter="url(#shadowGlow)">
      <animate attributeName="opacity" values="0.2;0.4;0.2" dur="4s" repeatCount="indefinite"/>
    </rect>

    <!-- Main text -->
    <text id="matrixText" x="25" y="70" fill="url(#matrixGradient)" font-size="48" font-weight="800" filter="url(#matrixGlow)" font-family="'Courier New', monospace">
      Hi, I'm Tejas 👋
    </text>

    <!-- Animated underline -->
    <g id="underline">
      <line x1="25" y1="85" x2="650" y2="85" stroke="url(#matrixGradient)" stroke-width="3" stroke-linecap="round" filter="url(#matrixGlow)"/>
      <circle cx="25" cy="85" r="4" fill="#00ff41" filter="url(#matrixGlow)">
        <animate attributeName="r" values="4;6;4" dur="3s" repeatCount="indefinite"/>
      </circle>
      <circle cx="650" cy="85" r="4" fill="#00ff41" filter="url(#matrixGlow)">
        <animate attributeName="r" values="4;6;4" dur="3s" repeatCount="indefinite"/>
      </circle>
    </g>

    <!-- Floating matrix characters -->
    <text x="680" y="40" fill="#00ff41" font-size="16" opacity="0.4" font-family="'Courier New', monospace" filter="url(#matrixGlow)">
      <tspan>λ</tspan>
      <animate attributeName="opacity" values="0.2;0.6;0.2" dur="2.5s" repeatCount="indefinite"/>
    </text>
    <text x="15" y="105" fill="#00ff41" font-size="14" opacity="0.3" font-family="'Courier New', monospace" filter="url(#matrixGlow)">
      <tspan>→</tspan>
      <animate attributeName="opacity" values="0.2;0.5;0.2" dur="3.2s" repeatCount="indefinite"/>
    </text>
  </svg>

  <p>
    <strong>Developer • Builder • Lifelong learner</strong>
  </p>

  <p>
    <a href="https://github.com/TejasGov">
      <img src="https://komarev.com/ghpvc/?username=TejasGov&style=flat-square" alt="Profile views" />
    </a>
    <a href="https://www.linkedin.com/in/tejas-govind-29520a2b2/">
      <img src="https://img.shields.io/badge/LinkedIn-0077B5?style=flat-square&logo=linkedin&logoColor=white" alt="LinkedIn" />
    </a>
    <a href="mailto:tejasgov2005@gmail.com">
      <img src="https://img.shields.io/badge/Gmail-D14836?style=flat-square&logo=gmail&logoColor=white" alt="Gmail" />
    </a>
  </p>

  <p>
    <a href="https://www.youtube.com/@tejasgovind">
      <img src="https://img.shields.io/badge/YouTube-FF0000?style=flat-square&logo=youtube&logoColor=white" alt="YouTube" />
    </a>
    <a href="https://www.instagram.com/tejasgovind_/">
      <img src="https://img.shields.io/badge/Instagram-E4405F?style=flat-square&logo=instagram&logoColor=white" alt="Instagram" />
    </a>
    <a href="https://www.kaggle.com/tejasgovind">
      <img src="https://img.shields.io/badge/Kaggle-20BEFF?style=flat-square&logo=kaggle&logoColor=white" alt="Kaggle" />
    </a>
    <a href="https://tejasgovind.wordpress.com/">
      <img src="https://img.shields.io/badge/WordPress-21759B?style=flat-square&logo=wordpress&logoColor=white" alt="WordPress" />
    </a>
    <a href="https://x.com/TejasGovin17982">
      <img src="https://img.shields.io/badge/X-000000?style=flat-square&logo=x&logoColor=white" alt="X" />
    </a>
    <a href="https://www.hackerrank.com/profile/tejasgovind3">
      <img src="https://img.shields.io/badge/HackerRank-00EA64?style=flat-square&logo=hackerrank&logoColor=white" alt="HackerRank" />
    </a>
  </p>
</div>

<br clear="right" />
<div align="left">

<pre>
████████╗███████╗     ██╗ █████╗ ███████╗
╚══██╔══╝██╔════╝     ██║██╔══██╗██╔════╝
   ██║   █████╗       ██║███████║███████╗
   ██║   ██╔══╝  ██   ██║██╔══██║╚════██║
   ██║   ███████╗╚█████╔╝██║  ██║███████║
   ╚═╝   ╚══════╝ ╚════╝ ╚═╝  ╚═╝╚══════╝
</pre>

</div>
---

## About me

I'm Tejas, a developer who likes building things that feel as good as they work. I enjoy working across the stack, from clean frontend interfaces with React and Next.js to backend systems with Node.js, APIs, and data-driven features. I care about product thinking, user experience, and turning rough ideas into polished experiences.

I'm drawn to projects where engineering meets creativity. That could be a full-stack web app, a real-time feature, a game prototype, a machine learning experiment, or a polished UI that makes an experience feel special.

Outside of code, I'm into design, games, content creation, and exploring new tools that help me build better. I share my work across GitHub, YouTube, Kaggle, WordPress, and other platforms because I like building and learning in public.

Right now, I'm focused on becoming a stronger builder, improving my technical depth, and creating projects that are practical, polished, and worth showing off.

---

## 💻 Tech Stack:

<table align="center">
  <tr>
    <td align="center" width="70">
      <a href="https://aws.amazon.com" target="_blank" rel="noreferrer">
        <img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/amazonwebservices/amazonwebservices-original-wordmark.svg" width="45" height="45" alt="aws" />
      </a>
    </td>
    <td align="center" width="70">
      <a href="https://www.cprogramming.com/" target="_blank" rel="noreferrer">
        <img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/c/c-original.svg" width="45" height="45" alt="c" />
      </a>
    </td>
    <td align="center" width="70">
      <a href="https://www.w3schools.com/css/" target="_blank" rel="noreferrer">
        <img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/css3/css3-original-wordmark.svg" width="45" height="45" alt="css3" />
      </a>
    </td>
    <td align="center" width="70">
      <a href="https://expressjs.com" target="_blank" rel="noreferrer">
        <img src="https://icon.icepanel.io/Technology/svg/Azure.svg" />
      </a>
    </td>
    <td align="center" width="70">
      <a href="https://www.figma.com/" target="_blank" rel="noreferrer">
        <img src="https://www.vectorlogo.zone/logos/figma/figma-icon.svg" width="45" height="45" alt="figma" />
      </a>
    </td>
    <td align="center" width="70">
      <a href="https://firebase.google.com/" target="_blank" rel="noreferrer">
        <img src="https://www.vectorlogo.zone/logos/firebase/firebase-icon.svg" width="45" height="45" alt="firebase" />
      </a>
    </td>
    <td align="center" width="70">
      <a href="https://www.framer.com/" target="_blank" rel="noreferrer">
        <img src="https://www.vectorlogo.zone/logos/framer/framer-icon.svg" width="45" height="45" alt="framer" />
      </a>
    </td>
    <td align="center" width="70">
      <a href="https://cloud.google.com" target="_blank" rel="noreferrer">
        <img src="https://www.vectorlogo.zone/logos/google_cloud/google_cloud-icon.svg" width="45" height="45" alt="gcp" />
      </a>
    </td>
  </tr>
  <tr>
    <td align="center" width="70">
      <a href="https://www.w3.org/html/" target="_blank" rel="noreferrer">
        <img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/html5/html5-original-wordmark.svg" width="45" height="45" alt="html5" />
      </a>
    </td>
    <td align="center" width="70">
      <a href="https://www.java.com" target="_blank" rel="noreferrer">
        <img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/java/java-original.svg" width="45" height="45" alt="java" />
      </a>
    </td>
    <td align="center" width="70">
      <a href="https://developer.mozilla.org/en-US/docs/Web/JavaScript" target="_blank" rel="noreferrer">
        <img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/javascript/javascript-original.svg" width="45" height="45" alt="javascript" />
      </a>
    </td>
    <td align="center" width="70">
      <a href="https://www.mongodb.com/" target="_blank" rel="noreferrer">
        <img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/mongodb/mongodb-original-wordmark.svg" width="45" height="45" alt="mongodb" />
      </a>
    </td>
    <td align="center" width="70">
      <a href="https://www.mysql.com/" target="_blank" rel="noreferrer">
        <img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/mysql/mysql-original-wordmark.svg" width="45" height="45" alt="mysql" />
      </a>
    </td>
    <td align="center" width="70">
      <a href="https://nextjs.org/" target="_blank" rel="noreferrer">
        <img src="https://icon.icepanel.io/Technology/png-shadow-512/Next.js.png" />
      </a>
    </td>
    <td align="center" width="70">
      <a href="https://nodejs.org" target="_blank" rel="noreferrer">
        <img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/nodejs/nodejs-original-wordmark.svg" width="45" height="45" alt="nodejs" />
      </a>
    </td>
    <td align="center" width="70">
      <a href="https://opencv.org/" target="_blank" rel="noreferrer">
        <img src="https://www.vectorlogo.zone/logos/opencv/opencv-icon.svg" width="45" height="45" alt="opencv" />
      </a>
    </td>
  </tr>
  <tr>
    <td align="center" width="70">
      <a href="https://pandas.pydata.org/" target="_blank" rel="noreferrer">
        <img src="https://raw.githubusercontent.com/devicons/devicon/2ae2a900d2f041da66e950e4d48052658d850630/icons/pandas/pandas-original.svg" width="45" height="45" alt="pandas" />
      </a>
    </td>
    <td align="center" width="70">
      <a href="https://www.photoshop.com/en" target="_blank" rel="noreferrer">
        <img src="https://icon.icepanel.io/Technology/svg/Adobe-Premiere-Pro.svg" />
      </a>
    </td>
    <td align="center" width="70">
      <a href="https://www.python.org" target="_blank" rel="noreferrer">
        <img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/python/python-original.svg" width="45" height="45" alt="python" />
      </a>
    </td>
    <td align="center" width="70">
      <a href="https://pytorch.org/" target="_blank" rel="noreferrer">
        <img src="https://www.vectorlogo.zone/logos/pytorch/pytorch-icon.svg" width="45" height="45" alt="pytorch" />
      </a>
    </td>
    <td align="center" width="70">
      <a href="https://reactjs.org/" target="_blank" rel="noreferrer">
        <img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/react/react-original-wordmark.svg" width="45" height="45" alt="react" />
      </a>
    </td>
    <td align="center" width="70">
      <a href="https://scikit-learn.org/" target="_blank" rel="noreferrer">
        <img src="https://upload.wikimedia.org/wikipedia/commons/0/05/Scikit_learn_logo_small.svg" width="45" height="45" alt="scikit_learn" />
      </a>
    </td>
    <td align="center" width="70">
      <a href="https://tailwindcss.com/" target="_blank" rel="noreferrer">
        <img src="https://www.vectorlogo.zone/logos/tailwindcss/tailwindcss-icon.svg" width="45" height="45" alt="tailwind" />
      </a>
    </td>
    <td align="center" width="70">
      <a href="https://www.tensorflow.org" target="_blank" rel="noreferrer">
        <img src="https://www.vectorlogo.zone/logos/tensorflow/tensorflow-icon.svg" width="45" height="45" alt="tensorflow" />
      </a>
    </td>
  </tr>
  <tr>
    <td align="center" width="70">
      <a href="https://www.typescriptlang.org/" target="_blank" rel="noreferrer">
        <img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/typescript/typescript-original.svg" width="45" height="45" alt="typescript" />
      </a>
    </td>
    <td align="center" width="70">
      <a href="https://vuejs.org/" target="_blank" rel="noreferrer">
        <img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/vuejs/vuejs-original-wordmark.svg" width="45" height="45" alt="vuejs" />
      </a>
    </td>
    <td align="center" width="70">
      <a href="https://vuejs.org/" target="_blank" rel="noreferrer">
        <img src="https://raw.githubusercontent.com/lobehub/lobe-icons/refs/heads/master/packages/static-png/light/antigravity-color.png" width="45" height="45" alt="vuejs" />
      </a>
    </td>
    <td align="center" width="70">
      <a href="https://vuejs.org/" target="_blank" rel="noreferrer">
        <img src="https://devicons.io/devicons/icons/openclaw.svg" width="45" height="45" alt="vuejs" />
      </a>
    </td>
    <td align="center" width="70">
      <a href="https://vuejs.org/" target="_blank" rel="noreferrer">
        <img src="https://devicons.io/devicons/icons/lovable-icon.svg" width="45" height="45" alt="vuejs" />
      </a>
    </td>
    <td align="center" width="70">
      <a href="https://vuejs.org/" target="_blank" rel="noreferrer">
        <img src="https://devicons.io/devicons/icons/claude-code.svg" width="45" height="45" alt="vuejs" />
      </a>
    </td>
    <td align="center" width="70">
      <a href="https://vuejs.org/" target="_blank" rel="noreferrer">
        <img src="https://devicons.io/devicons/icons/kubernetes.svg" width="45" height="45" alt="vuejs" />
      </a>
    </td>
  </tr>
</table>

---

## 📊 GitHub Stats:

<div align="center">
  <img src="https://streak-stats.demolab.com?user=TejasGov&locale=en&mode=daily&theme=dracula&hide_border=true&border_radius=5&order=3" height="150" alt="streak graph" />
</div>

<div align="center" style="margin-top: 15px;">
  <h3>Languages</h3>
  <img alt="TypeScript" src="https://img.shields.io/badge/TypeScript-29%25-3178c6?style=flat" />
  <img alt="JavaScript" src="https://img.shields.io/badge/JavaScript-23%25-f7df1e?style=flat" />
  <img alt="Python" src="https://img.shields.io/badge/Python-18%25-3776ab?style=flat" />
  <img alt="HTML" src="https://img.shields.io/badge/HTML-15%25-e34c26?style=flat" />
  <img alt="Jupyter Notebook" src="https://img.shields.io/badge/Jupyter-10%25-f37726?style=flat" />
  <img alt="GDScript" src="https://img.shields.io/badge/GDScript-5%25-355570?style=flat" />
</div>

---

## 🕹️ Contribution Graph:

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/TejasGov/TejasGov/output/pacman-contribution-graph-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/TejasGov/TejasGov/output/pacman-contribution-graph.svg">
  <img alt="pacman contribution graph" src="https://raw.githubusercontent.com/TejasGov/TejasGov/output/pacman-contribution-graph.svg">
</picture>
