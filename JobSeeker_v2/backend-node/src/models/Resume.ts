import mongoose from 'mongoose';

const ResumeSchema = new mongoose.Schema({
  userId: { type: String, required: true },
  parsedData: { type: Object, required: true },
  version: { type: Number, default: 1 },
  createdAt: { type: Date, default: Date.now },
});

export const Resume = mongoose.model('Resume', ResumeSchema);
