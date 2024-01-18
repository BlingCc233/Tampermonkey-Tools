#include <iostream>
#include <fstream>
#include <vector>
#include <string>

void mergeFiles(const std::string& indexFilePath)
{
    std::ifstream indexFile(indexFilePath);
    std::string line;
    std::vector<std::string> fileNames;

    while (std::getline(indexFile, line)) {
        fileNames.push_back(line);
    }

    std::string originalFilename = fileNames.back();

    fileNames.pop_back();

    std::ofstream outputFile(originalFilename);

    for (const auto& fileName : fileNames) {
        std::ifstream inputFile(fileName, std::ios::binary);
        outputFile << inputFile.rdbuf();
    }

    std::cout << "Files merged successfully.\n";
}

int main(int argc, char* argv[]) {
    if (argc < 2) {
        std::cerr << "Usage: " << argv[0] << " <txt_file>" << std::endl;
        return 1;
    }

    std::string txtFile = argv[1];
    mergeFiles(txtFile);

    return 0;
}
//
// Created by Cc Bling on 2024/1/17.
//
