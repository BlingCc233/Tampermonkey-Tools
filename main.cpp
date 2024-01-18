#include <iostream>
#include <fstream>
#include <vector>
#include <filesystem>

namespace fs = std::filesystem;

const std::size_t maxFileSize = 50 * 1024 * 1024; // 50 MB

void splitFile(const std::string& inputFile) {
    std::ifstream file(inputFile, std::ios::binary);
    if (!file.is_open()) {
        std::cerr << "Error: Unable to open file: " << inputFile << std::endl;
        return;
    }

    fs::create_directory(inputFile + "_split");
    std::ofstream txtFile(inputFile + "_split/file_mapping.txt");

    std::size_t partNum = 0;
    while (file) {
        std::vector<char> buffer(maxFileSize);
        file.read(buffer.data(), maxFileSize);

        std::string partFileName = inputFile + "_split/" + fs::path(inputFile).filename().string() + ".part" + std::to_string(partNum);
        std::ofstream partFile(partFileName, std::ios::binary);
        partFile.write(buffer.data(), file.gcount());
        partFile.close();

        txtFile << fs::path(partFileName).filename().string() << std::endl;

        partNum++;
    }

    txtFile << fs::path(inputFile).filename().string();

    txtFile.close();
    std::cout << "Splitting complete." << std::endl;
}

int main(int argc, char* argv[]) {
    if (argc < 2) {
        std::cerr << "Usage: " << argv[0] << " <input_file>" << std::endl;
        return 1;
    }

    std::string inputFile = argv[1];
    splitFile(inputFile);

    return 0;
}
