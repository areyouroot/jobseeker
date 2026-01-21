import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import passport from 'passport';
import { connectPostgres } from './src/config/postgres';
import { connectMongo } from './src/config/mongo';
import authRoutes from './src/routes/auth';
import paymentRoutes from './src/routes/payment';
import resumeRoutes from './src/routes/resume';

dotenv.config();

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());
app.use(passport.initialize());

// Routes
app.use('/auth', authRoutes);
app.use('/api/payment', paymentRoutes);
app.use('/api/resume', resumeRoutes);

app.get('/', (req, res) => {
  res.send('JobSeeker v2 Orchestrator is running');
});

const startServer = async () => {
  await connectPostgres();
  await connectMongo();
  app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
  });
};

startServer();
