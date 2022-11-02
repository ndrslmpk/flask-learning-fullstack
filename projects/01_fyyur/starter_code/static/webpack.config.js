const webpack = require('webpack');
const path = require('path');

const config = {
  mode: 'development',
  devtool: 'source-map',
  entry: './js/index.js',
  output: {
      path: path.resolve(__dirname, 'dist'),
      filename: 'main.bundle.js',  
  },
  resolve: {
      extensions: ['.js', '.jsx', '.css']
  },
  module: {
  }
};
module.exports = config;