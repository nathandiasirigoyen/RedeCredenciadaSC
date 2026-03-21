const { S3Client } = require("@aws-sdk/client-s3");
const { Upload } = require("@aws-sdk/lib-storage");
const mime = require("mime-types");
const fs = require("fs");
const path = require("path");
const { glob } = require("glob");

// --- CONFIGURAÇÃO ---
const BUCKET_NAME = "AQUI O BUCKET";
const ACCOUNT_ID = "-"; // Está na URL do endpoint
const ACCESS_KEY = "-";
const SECRET_KEY = "-";
const FOLDER_TO_UPLOAD = "./public"; //
// --------------------

const s3 = new S3Client({
  region: "auto",
  endpoint: `https://${ACCOUNT_ID}.r2.cloudflarestorage.com`,
  credentials: { accessKeyId: ACCESS_KEY, secretAccessKey: SECRET_KEY },
});

async function run() {
  console.log("Mapeando arquivos...");
  const files = await glob(`${FOLDER_TO_UPLOAD}/**/*`, { nodir: true });
  console.log(`Encontrados ${files.length} arquivos. Iniciando upload...`);

  // Upload em lotes para não travar
  const batchSize = 20; 
  for (let i = 0; i < files.length; i += batchSize) {
    const batch = files.slice(i, i + batchSize);
    await Promise.all(batch.map(file => uploadFile(file)));
    console.log(`Progresso: ${i + batch.length}/${files.length}`);
  }
}

async function uploadFile(filePath) {
  const fileStream = fs.createReadStream(filePath);
  const contentType = mime.lookup(filePath) || "application/octet-stream";
  const relativeKey = path.relative(FOLDER_TO_UPLOAD, filePath).replace(/\\/g, "/");

  try {
    const upload = new Upload({
      client: s3,
      params: {
        Bucket: BUCKET_NAME,
        Key: relativeKey,
        Body: fileStream,
        ContentType: contentType,
      },
    });
    await upload.done();
  } catch (e) {
    console.error(`Erro ao subir ${relativeKey}:`, e);
  }
}

run();