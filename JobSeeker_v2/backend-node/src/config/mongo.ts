import mongoose from 'mongoose';
import dotenv from 'dotenv';

dotenv.config();

export const connectMongo = async () => {
  try {
    const uri = process.env.MONGO_URI || 'mongodb://localhost:27017/jobseeker';
    await mongoose.connect(uri);
    console.log('MongoDB connected.');
  } catch (error) {
    console.error('Unable to connect to MongoDB:', error);
  }
};
