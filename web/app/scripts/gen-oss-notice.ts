import * as fs from "fs";
import * as glob from "glob";
import * as path from "path";

interface Package {
  name: string;
  version: string;
  license?: string | { type: string };
  licenses?: Array<{ type: string }>;
}

interface PackageMeta {
  name: string;
  version: string;
  licenses: string[];
}

const fixLicenses = (pkg: PackageMeta): PackageMeta => {
  if (pkg.name === "node-forge") {
    return {
      name: pkg.name,
      version: pkg.version,
      licenses: ["BSD-3-CLAUSE"],
    };
  }
  return pkg;
};

const getLicenses = (pkgPath: string): PackageMeta => {
  if (pkgPath.includes("@")) {
    return {
      name: pkgPath,
      version: "UNKNOWN",
      licenses: ["BYPASS"],
    };
  }

  const packageJsonPath = path.join(pkgPath, "package.json");
  let licenses: string[] = [];
  let version: string;
  try {
    const packageJsonFile = fs.readFileSync(packageJsonPath, "utf-8");
    const packageJson: Package = JSON.parse(packageJsonFile);
    version = packageJson.version;

    const license =
      packageJson.license ||
      packageJson.licenses ||
      "No license information found";
    if (typeof license === "string") {
      licenses = [license.toUpperCase()];
    } else if (Array.isArray(license)) {
      licenses = license.map((l) => l.type.toUpperCase());
    } else if (typeof license === "object") {
      licenses = [license.type.toUpperCase()];
    } else {
      throw new Error(`Unknown license type: ${license}`);
    }
  } catch (error) {
    // eslint-disable-next-line no-console
    const error_E = error as Error;
    console.error(
      `Error reading package.json for ${pkgPath}: ${error_E.message}`
    );
    licenses = ["BYPASS"];
    version = "UNKNOWN";
  }
  return {
    name: path.basename(pkgPath),
    version,
    licenses,
  };
};

const reviseLicenses = (pkg: PackageMeta): PackageMeta => {
  const revisedLicenses: string[] = [];
  pkg.licenses.forEach((license) => {
    if (license.includes(" OR ")) {
      license.split(" OR ").forEach((l) => revisedLicenses.push(l));
    } else {
      revisedLicenses.push(license);
    }
  });
  return {
    name: pkg.name,
    version: pkg.version,
    licenses: revisedLicenses.map((l) =>
      l.toUpperCase().replace("(", "").replace(")", "")
    ),
  };
};

const getLicenseBody = (licensePath: string, license: string): string => {
  try {
    const lists = glob.sync(`${licensePath.replace(/\\/g, "/")}/*LICENSE*`);
    if (lists.length > 0) {
      return fs.readFileSync(lists[0], "utf-8");
    }
    const lists2 = glob.sync(`${licensePath.replace(/\\/g, "/")}/*COPYING*`);
    if (lists2.length > 0) {
      return fs.readFileSync(lists2[0], "utf-8");
    }
    const lists3 = glob.sync(`${licensePath.replace(/\\/g, "/")}/*LICENCE*`);
    if (lists3.length > 0) {
      return fs.readFileSync(lists3[0], "utf-8");
    }
    throw new Error("No license file found");
  } catch {
    // eslint-disable-next-line no-console
    return `License: ${license}

Sorry, no license file found. This OSS notice file is automatically generated
from the distributed module package.`;
  }
};

function checkLicenses(license: string): boolean | string {
  const freeLicenses = [
    "CC0-1.0",
    "0BSD",
    "Unlicense",
    "UNLICENSED",
    "BYPASS",
  ].map((l) => l.toUpperCase());
  const noticeRequiredLicenses = [
    "AFL-2.1",
    "AFL-3.0",
    "Artistic-1.0",
    "Artistic-2.0",
    "Apache-1.1",
    "Apache-2.0",
    "BLUEOAK-1.0.0",
    "BSL-1.0",
    "BSD-2-Clause",
    "BSD-3-Clause",
    "BSD-2-Clause-Patent",
    "CC-BY-4.0",
    "CC-BY-3.0",
    "JSON",
    "FTL",
    "ISC",
    "IJG",
    "libtiff",
    "LPL-1.02",
    "MS-PL",
    "MIT",
    "X11",
    "MIT-CMU",
    "NCSA",
    "OpenSSL",
    "PHP-3.0",
    "PostgreSQL",
    "PYTHON-2.0",
    "TCP-wrappers",
    "PSF-2.0",
    "Unicode-DFS-2016",
    "UPL-1.0",
    "W3C",
    "Xnet",
    "Zend-2.0",
    "zlib",
    "ZPL-2.0",
  ].map((l) => l.toUpperCase());
  const deniedLicenses = [
    "CC-BY-NC-4.0",
    "CC-BY-NC-ND-4.0",
    "CC-BY-NC-SA-4.0",
    "AGPL-3.0",
    "SSPL-1.0",
    "BSD-4-Clause",
    "GPL-2.0",
    "GPL-3.0",
    "CC-BY-SA-4.0",
    "CC-BY-ND-4.0",
    "OSL-3.0",
    "QPL-1.0",
    "Sleepycat",
  ].map((l) => l.toUpperCase());
  const weakCopyleftLicenses = [
    "LGPL-2.1",
    "LGPL-3.0",
    "CDDL-1.0",
    "CPL-1.0",
    "EPL-1.0",
    "EPL-2.0",
    "IPL-1.0",
    "MPL-1.1",
    "MPL-2.0",
    "APSL-2.0",
    "Ruby",
  ].map((l) => l.toUpperCase());
  if (freeLicenses.includes(license)) {
    return false;
  }
  if (deniedLicenses.includes(license)) {
    return `license ${license} is not allowed`;
  }
  if (weakCopyleftLicenses.includes(license)) {
    return `license ${license} is weak copyleft`;
  }
  if (noticeRequiredLicenses.includes(license)) {
    return true;
  }
  return `license ${license} is not checked`;
}

function generateOSSNotice(): void {
  const nodeModulesDir = "./node_modules";

  const packages: PackageMeta[] = fs
    .readdirSync(nodeModulesDir)
    .filter((name: string) => !name.startsWith("."))
    .map((name: string) => {
      const pkgPath = path.join(nodeModulesDir, name);
      const licenses = getLicenses(pkgPath);
      return fixLicenses(reviseLicenses(licenses));
    }) as PackageMeta[];

  let notices = packages.reduce((_notices: string, pkg: PackageMeta) => {
    const checkResults = pkg.licenses.map((license) => checkLicenses(license));

    checkResults.forEach((result) => {
      if (typeof result === "string") {
        // eslint-disable-next-line no-console
        console.error(`Error checking license for ${pkg.name}: ${result}`);
      }
    });
    const noticeRequired = checkResults.some((result) => result === true);
    if (noticeRequired) {
      const lbody = getLicenseBody(
        path.join(nodeModulesDir, pkg.name),
        pkg.licenses.join(", ")
      ).replace(/`/g, "\\`");
      // NOTE : exposing version is not a good idea for security reasons.
      const notice = `
      <Typography variant="h6" gutterBottom component="div">
        ${pkg.name}
      </Typography>
      <Typography variant="body2" sx={{ fontSize: "0.65rem" }} gutterBottom component="div">
        Version: ${pkg.version}
      </Typography>
      <Typography variant="body2" sx={{ fontSize: "0.65rem" }} gutterBottom component="div">
        <pre style={{ whiteSpace: 'pre-wrap', fontFamily: "'Fira Mono', monospace" }}>
          {\`${lbody}\`}
        </pre>
      </Typography>`;
      return _notices + notice;
    }
    return _notices;
  }, "");

  const header = `import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';

const OSSNoticeContent = () => {
  return (
    <Box sx={{ typography: 'body1' }}>`;

  const footer = `
      <hr />
      <Typography variant="body1" gutterBottom component="div" sx={{ opacity: .5 }}>
        End of OSS list.
      </Typography>
    </Box>
  );
};

export default OSSNoticeContent;
`;

  fs.writeFile(
    "./src/components/main/TopPanel/OSSNoticeContent.tsx",
    header + notices + footer,
    {
      encoding: "utf-8",
      flag: "w",
    },
    (error) => {
      if (error) {
        // eslint-disable-next-line no-console
        console.error(error);
      } else {
        // eslint-disable-next-line no-console
        console.log("OSS notice generated.");
      }
    }
  );
}

generateOSSNotice();
