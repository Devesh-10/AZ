import dotenv from "dotenv";
dotenv.config();

import express from "express";
import cors from "cors";
import { queryRouter } from "./routes/query";
import { healthRouter } from "./routes/health";

const app = express();
const PORT = process.env.PORT || 3001;

app.use(cors());
app.use(express.json());

// Routes
app.use("/api/health", healthRouter);
app.use("/api/chat", queryRouter);

app.listen(PORT, () => {
  console.log(`MIA Backend running on port ${PORT}`);
});
