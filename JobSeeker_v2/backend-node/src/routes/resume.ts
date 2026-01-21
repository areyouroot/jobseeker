import { Router } from 'express';
import multer from 'multer';
import axios from 'axios';
import fs from 'fs';
import FormData from 'form-data';
import { Resume } from '../models/Resume';

const router = Router();
const upload = multer({ dest: 'uploads/' });

router.post('/upload', upload.single('file'), async (req, res) => {
  if (!req.file) return res.status(400).send('No file uploaded');

  try {
    // Send to Python Service
    const form = new FormData();
    form.append('file', fs.createReadStream(req.file.path), req.file.originalname);

    const pythonServiceUrl = process.env.AI_SERVICE_URL || 'http://localhost:8000';
    const response = await axios.post(`${pythonServiceUrl}/parse`, form, {
      headers: form.getHeaders(),
    });

    const parsedData = response.data;

    // Save to Mongo
    // Mock User ID for now
    const resume = new Resume({
      userId: 'mock-user-id',
      parsedData,
    });
    await resume.save();

    // Cleanup
    fs.unlinkSync(req.file.path);

    res.json({ id: resume._id, data: parsedData });
  } catch (error) {
    console.error(error);
    res.status(500).send('Error processing resume');
  }
});

router.post('/optimize', async (req, res) => {
  const { resumeId, instructions, model } = req.body;

  try {
    const resume = await Resume.findById(resumeId);
    if (!resume) return res.status(404).send('Resume not found');

    const pythonServiceUrl = process.env.AI_SERVICE_URL || 'http://localhost:8000';
    const response = await axios.post(`${pythonServiceUrl}/generate`, {
      context: resume.parsedData,
      prompt: instructions,
      model: model || 'ollama'
    });

    res.json(response.data);
  } catch (error) {
    res.status(500).send('Optimization failed');
  }
});

export default router;
