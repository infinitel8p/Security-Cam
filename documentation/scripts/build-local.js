const { execSync } = require("child_process");

execSync("npx docusaurus build --out-dir ../server/public/docs", {
  stdio: "inherit",
  env: { ...process.env, DOCS_URL: "http://localhost", DOCS_BASE_URL: "/docs/" },
});
